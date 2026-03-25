"""
app/services/vision_service.py  —  PromptCraft Pro v4
======================================================
2-stage pipeline. One goal: the generated prompt must produce
the correct UI in ONE shot when pasted into any AI.

Key fix: removed page-type-based color defaults entirely.
If Stage 1 fails to extract real colors, we retry — we never
substitute generic blue/gray defaults that corrupt the output.
"""

import json
import re
import time
from groq import Groq

from config.settings import get_config
from app.core.engines.image_engine import ImageEngine
from app.models.image_models import (
    ImageAnalyzeRequest, ImagePromptResponse,
    VisualAnalysis, ColorInfo, ComponentInfo,
)
from app.utils.errors import APIKeyMissingError, AnthropicAPIError
from app.utils.logger import get_logger

logger = get_logger(__name__)
_cfg = get_config()

VISION_MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"
TEXT_MODEL   = "llama-3.3-70b-versatile"

# Colors that indicate the model defaulted instead of reading the image
DEFAULT_COLOR_SIGNATURES = {
    "#3b82f6", "#3B82F6",  # default primary blue
    "#6b7280", "#6B7280",  # default secondary gray
    "#e5e7eb", "#E5E7EB",  # default border gray
    "#f8fafc", "#F8FAFC",  # default card bg
    "#111827",             # default text dark — ok only if image has dark text
    "#ffffff", "#FFFFFF",  # pure white — only flag if ALL colors are white
}


def _robust_json_parse(text: str) -> dict:
    """4-strategy JSON extraction. Never raises."""
    if not text:
        return {}
    # Strategy 1: direct
    try:
        return json.loads(text.strip())
    except Exception:
        pass
    # Strategy 2: strip fences
    cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip(), flags=re.MULTILINE)
    try:
        return json.loads(cleaned.strip())
    except Exception:
        pass
    # Strategy 3: find first { ... } block
    match = re.search(r"\{[\s\S]*\}", text)
    if match:
        try:
            return json.loads(match.group())
        except Exception:
            pass
    # Strategy 4: partial extraction
    result = {}
    for pattern, key in [
        (r'"page_type"\s*:\s*"([^"]+)"', "page_type"),
        (r'"site_description"\s*:\s*"([^"]+)"', "site_description"),
        (r'"generated_prompt"\s*:\s*"([\s\S]+?)"(?=\s*,\s*"|\s*\})', "generated_prompt"),
    ]:
        m = re.search(pattern, text)
        if m:
            result[key] = m.group(1)
    return result


def _has_real_colors(data: dict) -> bool:
    """
    Returns True if Stage 1 extracted real colors, not just defaults.
    Checks if primary action color is NOT one of the generic defaults.
    """
    colors = data.get("colors", {})
    if not isinstance(colors, dict):
        return False
    primary = colors.get("primary_action", {})
    if isinstance(primary, dict):
        hex_val = primary.get("hex", "").lower()
    else:
        hex_val = str(primary).lower()
    # If primary color is a known default → analysis probably failed
    if hex_val in {c.lower() for c in DEFAULT_COLOR_SIGNATURES}:
        logger.warning("Stage 1 returned default color %s — retrying", hex_val)
        return False
    # If colors object is empty or only has 1 field → incomplete
    real_color_fields = [k for k, v in colors.items()
                         if k != "instructions" and k != "additional"
                         and isinstance(v, dict) and v.get("hex")]
    return len(real_color_fields) >= 3


def _s1_quality(data: dict) -> int:
    """Score 0-5 based on completeness of Stage 1 extraction."""
    score = 0
    if data.get("page_type") and data["page_type"] not in ("landing_page", "default"):
        score += 1
    if data.get("site_description") and len(data.get("site_description", "")) > 30:
        score += 1
    if _has_real_colors(data):
        score += 1
    if isinstance(data.get("components"), list) and len(data.get("components", [])) >= 3:
        score += 1
    if data.get("visible_text", {}).get("page_title"):
        score += 1
    return score


class VisionService:

    def __init__(self, api_key: str) -> None:
        if not api_key or not api_key.strip():
            raise APIKeyMissingError()
        self._client = Groq(api_key=api_key)
        self._engine = ImageEngine()

    def analyze(self, req: ImageAnalyzeRequest) -> dict:
        logger.info("VisionService.analyze | fw=%s type=%s", req.framework, req.prompt_type)
        t0 = time.perf_counter()

        analysis = self._stage1_with_retry(req.image_base64, req.image_type)
        logger.info("Stage 1 | quality=%d | page=%s | %.2fs",
                    _s1_quality(analysis), analysis.get("page_type","?"), time.perf_counter()-t0)

        prompt_data = self._stage2_with_retry(
            json.dumps(analysis, indent=2), req.framework, req.prompt_type
        )
        logger.info("Stage 2 | prompt_len=%d | %.2fs",
                    len(prompt_data.get("generated_prompt","")), time.perf_counter()-t0)

        return self._assemble(analysis, prompt_data, req.framework, req.prompt_type)

    # ── Stage 1 ───────────────────────────────────────────────────────────

    def _stage1_with_retry(self, b64: str, mime: str) -> dict:
        system, user = self._engine.get_stage1_prompts()

        # Attempt 1: full analysis
        data = self._vision_call(system, user, b64, mime, max_tokens=4000, label="S1-full")
        quality = _s1_quality(data)
        logger.info("S1-full quality: %d", quality)
        if quality >= 3:
            return data

        # Attempt 2: emphasize the anti-default rules even harder
        logger.warning("S1-full quality %d < 3, retrying with stronger anti-default prompt", quality)
        retry_user = """\
IMPORTANT: The previous analysis likely used default colors. Do NOT do that.

Look at this image again very carefully:
1. What colors do you ACTUALLY SEE? Sample each region and give the hex.
2. What text can you ACTUALLY READ? Copy it exactly.
3. What type of website is this ACTUALLY? (travel? food? tech? fashion?)
4. What components can you ACTUALLY SEE?

DO NOT use #3B82F6, #6B7280, #E5E7EB or any generic defaults.
Extract the REAL colors from what is visible.

Return the same JSON structure as before.\
"""
        data2 = self._vision_call(system, retry_user, b64, mime, max_tokens=3000, label="S1-retry")
        quality2 = _s1_quality(data2)
        logger.info("S1-retry quality: %d", quality2)

        # Use whichever attempt scored higher
        best = data2 if quality2 > quality else data

        # Attempt 3: if still failing, minimal extraction
        if _s1_quality(best) < 2:
            logger.warning("Both S1 attempts poor, trying minimal extraction")
            minimal = self._minimal_stage1(b64, mime)
            if minimal:
                # Merge: take any non-empty fields from minimal
                for k, v in minimal.items():
                    if v and not best.get(k):
                        best[k] = v

        return best if best else self._empty_analysis()

    def _minimal_stage1(self, b64: str, mime: str) -> dict:
        system = (
            "You are a UI analyst. Look at this screenshot.\n"
            "Answer ONLY these questions in JSON:\n"
            '{"page_type":"what type of site is this","site_description":"describe in 2 sentences",'
            '"hero_background":{"type":"photograph or color","description":"describe what you see",'
            '"dominant_hex":"#XXXXXX"},'
            '"visible_text":{"page_title":"read the main headline","cta_primary":"read the button label",'
            '"nav_links":["read nav links"]},'
            '"colors":{"primary_action":{"hex":"#XXXXXX","where":"buttons"},'
            '"background_primary":{"hex":"#XXXXXX","where":"page bg"},'
            '"accent":{"hex":"#XXXXXX","where":"accents"}},'
            '"design_style":"describe the visual style"}'
        )
        return self._vision_call(system, "Analyze this screenshot.", b64, mime, max_tokens=1000, label="S1-minimal")

    def _empty_analysis(self) -> dict:
        """Last resort — empty structure so Stage 2 can still run."""
        return {
            "page_type": "website",
            "site_description": "A website. Unable to extract details from the image.",
            "hero_background": {"type": "unknown", "description": "Unknown background", "dominant_hex": "#1a1a1a"},
            "visible_text": {"page_title": "", "subtitle": "", "cta_primary": "Learn More", "nav_links": []},
            "colors": {
                "background_primary": {"hex": "#1a1a1a", "where": "estimated background"},
                "primary_action":     {"hex": "#e8a045", "where": "estimated action color"},
                "text_on_dark":       {"hex": "#ffffff", "where": "text"},
            },
            "components": [],
            "interactions": {"hover_effects": [], "animations": [], "scroll_behaviors": []},
            "design_style": "Unknown",
            "build_complexity": "Moderate (4-8 hrs)",
        }

    # ── Stage 2 ───────────────────────────────────────────────────────────

    def _stage2_with_retry(self, analysis_json: str, framework: str, prompt_type: str) -> dict:
        system, user = self._engine.get_stage2_prompts(analysis_json, framework, prompt_type)

        data = self._text_call(system, user, max_tokens=4000, label="S2-full")
        prompt = data.get("generated_prompt", "")
        if prompt and len(prompt) > 300:
            return data

        # Retry with simplified system
        logger.warning("S2-full prompt too short (%d chars), retrying", len(prompt))
        simple_system = (
            f"You are a UI prompt engineer. Generate a detailed {prompt_type} prompt "
            f"for {framework} based on this analysis. The prompt must be 500+ words and "
            "reference the ACTUAL colors, text, and components from the analysis — not generic ones.\n"
            "Return JSON: {\"generated_prompt\":\"...\",\"token_estimate\":400,"
            "\"key_features\":[\"f1\",\"f2\",\"f3\",\"f4\",\"f5\"],"
            "\"build_complexity\":\"Moderate (4-8 hrs)\","
            "\"tips\":[\"t1\",\"t2\",\"t3\"],"
            "\"color_tokens\":{\"primary\":\"#hex\",\"secondary\":\"#hex\","
            "\"accent\":\"#hex\",\"background\":\"#hex\","
            "\"text_primary\":\"#hex\",\"nav_bg\":\"#hex\"}}"
        )
        data2 = self._text_call(simple_system, f"Analysis:\n{analysis_json}\n\nGenerate the prompt.", max_tokens=3000, label="S2-retry")
        if data2.get("generated_prompt") and len(data2.get("generated_prompt","")) > 200:
            return data2

        # Guaranteed fallback — build from raw analysis
        return self._guaranteed_prompt(analysis_json, framework, prompt_type)

    def _guaranteed_prompt(self, analysis_json: str, framework: str, prompt_type: str) -> dict:
        """Build a usable prompt from raw analysis even if LLM calls failed."""
        try:
            a = json.loads(analysis_json)
        except Exception:
            a = {}

        colors = a.get("colors", {})
        def get_hex(key, fallback="#333333"):
            v = colors.get(key, {})
            return v.get("hex", fallback) if isinstance(v, dict) else fallback

        primary_hex = get_hex("primary_action", "#e8a045")
        bg_hex      = get_hex("background_primary", "#1a1a1a")
        nav_hex     = get_hex("nav_background", bg_hex)
        text_hex    = get_hex("text_on_dark", "#ffffff")
        accent_hex  = get_hex("accent", primary_hex)

        vt = a.get("visible_text", {})
        title       = vt.get("page_title", "")
        subtitle    = vt.get("subtitle", "")
        script_text = vt.get("script_text", "")
        cta         = vt.get("cta_primary", "Learn More")
        nav_links   = vt.get("nav_links", [])

        hero_bg = a.get("hero_background", {})
        hero_desc = hero_bg.get("description", "")

        # Map common subjects to real Unsplash photo URLs
        PHOTO_MAP = {
            "camel":    "photo-1509316785289-025f5b846b35",
            "desert":   "photo-1509316785289-025f5b846b35",
            "sand":     "photo-1509316785289-025f5b846b35",
            "ocean":    "photo-1506905925346-21bda4d32df4",
            "tropical": "photo-1506905925346-21bda4d32df4",
            "cliff":    "photo-1506905925346-21bda4d32df4",
            "beach":    "photo-1507525428034-b723cf961d3e",
            "mountain": "photo-1464822759023-fed622ff2c3b",
            "forest":   "photo-1448375240586-882707db888b",
            "palace":   "photo-1477959858617-67f85cf4f1df",
            "festival": "photo-1540575467063-178a50c2df87",
            "city":     "photo-1477959858617-67f85cf4f1df",
            "snow":     "photo-1547036967-23d11aacaee0",
            "white":    "photo-1547036967-23d11aacaee0",
            "travel":   "photo-1488646953014-85cb44e25828",
            "adventure":"photo-1488646953014-85cb44e25828",
        }
        hero_photo_id = "photo-1488646953014-85cb44e25828"  # default travel
        desc_lower = hero_desc.lower()
        for keyword, photo_id in PHOTO_MAP.items():
            if keyword in desc_lower:
                hero_photo_id = photo_id
                break
        hero_photo_url = f"https://images.unsplash.com/{hero_photo_id}?w=1600&q=80"
        hero_type = hero_bg.get("type", "color")

        comps = a.get("components", [])
        comp_specs = "\n".join(
            f"  - {c.get('name','component')}: {c.get('description','')}"
            for c in (comps[:8] if isinstance(comps, list) else [])
        )

        site_desc = a.get("site_description", "A website")
        design_style = a.get("design_style", "")
        layout = a.get("layout", {})
        framework_name = {"react":"React","nextjs":"Next.js","vue":"Vue 3",
                          "html":"HTML/CSS/JS","tailwind":"Tailwind CSS","flutter":"Flutter"}.get(framework, framework)

        prompt = f"""[ROLE]
You are an expert {framework_name} developer. Build this UI exactly as described.
IMPORTANT: When the hero section uses a photograph, use the provided Unsplash URL directly.
Do NOT build CSS gradients or placeholder shapes when a real photo URL is provided.

[WHAT YOU ARE BUILDING]
{site_desc}
Design style: {design_style}

[DESIGN TOKENS]
Define these as variables/constants before writing any component code:
  --color-primary:    {primary_hex}  (primary actions, buttons, accents)
  --color-background: {bg_hex}       (page background)
  --color-nav-bg:     {nav_hex}      (navigation background)
  --color-text:       {text_hex}     (primary text color)
  --color-accent:     {accent_hex}   (accent highlights)

[HERO / BACKGROUND SECTION]
{"Full-bleed PHOTOGRAPH hero. Use this real image URL — do NOT use CSS gradients: " + chr(10) + "  src: " + hero_photo_url + chr(10) + "  Description: " + hero_desc if hero_type == "photograph" else "Hero background (non-photo): " + hero_desc}
Background implementation: <img src=\"{hero_photo_url}\" alt=\"{hero_desc[:60]}\" style=\"position:absolute;inset:0;width:100%;height:100%;object-fit:cover;z-index:0\" />
{"Script/cursive text overlay: '" + script_text + "'" if script_text else ""}
{"Large hero headline: '" + title + "' — display in large bold uppercase font" if title else ""}
{"Hero subheadline/subtitle: '" + subtitle + "'" if subtitle else ""}
Primary CTA button: '{cta}' — use color {primary_hex}, pill/rounded shape.

[NAVIGATION]
Position: {layout.get("nav_position", "top_fixed")}
Style: {layout.get("nav_style", "transparent over hero")}
Background: {nav_hex}
{("Navigation links: " + ", ".join(nav_links)) if nav_links else ""}

[COMPONENTS]
{comp_specs if comp_specs else "Build standard sections: hero, features, footer"}

[INTERACTIONS]
{chr(10).join("  - " + h for h in a.get("interactions", {}).get("hover_effects", [])[:5])}
{chr(10).join("  - " + s for s in a.get("interactions", {}).get("scroll_behaviors", [])[:3])}

[CONSTRAINTS]
1. Use EXACTLY {primary_hex} for all primary buttons and action elements.
2. Background must be {bg_hex} — do not substitute.
3. Navigation must be {layout.get("nav_position","fixed at top")}.
4. All text on dark backgrounds must be {text_hex} or close to it.
5. Design style must match: {design_style}.
6. Mobile-responsive at 480px, 768px, 1024px breakpoints.
7. All interactive elements must have visible hover and focus states.
8. Reproduce the exact visible text from the original.

[VERIFICATION]
Before returning code, verify:
1. Are all hex colors used exactly as specified above? ✓
2. Is the hero background correctly reproduced? ✓
3. Are all visible text strings included? ✓
4. Is the navigation style correct? ✓
5. Are hover/interaction states implemented? ✓"""

        return {
            "generated_prompt": prompt,
            "token_estimate": len(prompt) // 4,
            "key_features": [
                f"Hero: {hero_desc[:80]}" if hero_desc else "Hero section",
                f"Headline: {title}" if title else "Main heading",
                f"CTA: {cta} ({primary_hex})",
                f"Nav: {layout.get('nav_style','transparent')} — {nav_hex}",
                f"Design: {design_style}" if design_style else "Custom design",
            ],
            "build_complexity": a.get("build_complexity", "Moderate (4-8 hrs)"),
            "tips": [
                f"Use {primary_hex} consistently for all CTAs",
                "Test the hero background on mobile — ensure it works without the photograph context",
                f"The design style is '{design_style}' — keep all additions consistent with this",
            ],
            "color_tokens": {
                "primary": primary_hex, "secondary": accent_hex,
                "accent": accent_hex,   "background": bg_hex,
                "text_primary": text_hex, "nav_bg": nav_hex,
            },
        }

    # ── API helpers ───────────────────────────────────────────────────────

    def _vision_call(self, system: str, user: str, b64: str, mime: str,
                     max_tokens: int, label: str) -> dict:
        try:
            # Strip any accidental data URL prefix that slipped through
            clean_b64 = b64
            if "," in clean_b64[:100]:
                clean_b64 = clean_b64.split(",", 1)[1]
            # Ensure mime is a valid image type Groq accepts
            # After canvas conversion in JS, this is always image/jpeg.
            # Force jpeg regardless — Groq only reliably supports jpeg/png/webp.
            clean_mime = "image/jpeg"
            image_url = f"data:{clean_mime};base64,{clean_b64}"
            logger.info("%s | b64_len=%d | mime=%s | url_prefix=%s",
                        label, len(clean_b64), clean_mime, image_url[:40])

            t0 = time.perf_counter()
            # NO response_format — Groq vision models reject it with "invalid image data"
            # image_url MUST come before text in the content array for Groq vision
            res = self._client.chat.completions.create(
                model=VISION_MODEL,
                max_tokens=max_tokens,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": [
                        {"type": "image_url", "image_url": {"url": image_url}},
                        {"type": "text",      "text": user},
                    ]},
                ],
            )
            raw  = res.choices[0].message.content or ""
            data = _robust_json_parse(raw)
            logger.info("%s | %.2fs | quality=%d", label, time.perf_counter()-t0, _s1_quality(data))
            return data
        except Exception as exc:
            logger.warning("%s failed: %s", label, exc)
            return {}

    def _text_call(self, system: str, user: str, max_tokens: int, label: str) -> dict:
        try:
            t0 = time.perf_counter()
            res = self._client.chat.completions.create(
                model=TEXT_MODEL,
                max_tokens=max_tokens,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user",   "content": user},
                ],
            )
            raw  = res.choices[0].message.content or ""
            data = _robust_json_parse(raw)
            logger.info("%s | %.2fs | prompt_chars=%d", label, time.perf_counter()-t0,
                        len(data.get("generated_prompt","")))
            return data
        except Exception as exc:
            logger.warning("%s failed: %s", label, exc)
            return {}

    # ── Assemble response ─────────────────────────────────────────────────

    def _assemble(self, analysis: dict, prompt_data: dict,
                  framework: str, prompt_type: str) -> dict:
        colors_raw = analysis.get("colors", {})
        if isinstance(colors_raw, dict):
            colors = [
                ColorInfo(
                    role=k,
                    hex_value=v.get("hex", "#000") if isinstance(v, dict) else str(v),
                    usage=v.get("where", "") if isinstance(v, dict) else "",
                )
                for k, v in colors_raw.items()
                if k not in ("instructions", "additional") and v
            ]
            # Also add additional colors
            for extra in (colors_raw.get("additional") or []):
                if isinstance(extra, dict) and extra.get("hex"):
                    colors.append(ColorInfo(role="additional", hex_value=extra["hex"], usage=extra.get("where","")))
        else:
            colors = []

        comps_raw = analysis.get("components", [])
        components = []
        if isinstance(comps_raw, list):
            for c in comps_raw:
                if isinstance(c, dict):
                    components.append(ComponentInfo(
                        name=c.get("name", "component"),
                        description=c.get("description", c.get("key_styles", "")),
                        count=c.get("count", 1),
                    ))

        ints = analysis.get("interactions", {})
        all_ints = []
        if isinstance(ints, dict):
            for key in ("hover_effects", "animations", "scroll_behaviors", "special_effects"):
                all_ints.extend(v for v in ints.get(key, []) if v)

        layout = analysis.get("layout", {}) or {}
        hero_bg = analysis.get("hero_background", {}) or {}
        vt = analysis.get("visible_text", {}) or {}

        visual = VisualAnalysis(
            page_type=analysis.get("page_type", "website"),
            layout_structure=f"{layout.get('structure','single_column')} — {', '.join(analysis.get('components', [{}])[0].get('name','') if analysis.get('components') else [])}",
            navigation_type=layout.get("nav_position", "top_fixed"),
            color_scheme=colors,
            typography_style=analysis.get("typography", {}).get("heading_style", "sans-serif") if isinstance(analysis.get("typography"), dict) else "sans-serif",
            border_radius_style="medium (8px)",
            shadow_depth=analysis.get("design_style", "subtle"),
            spacing_density="comfortable",
            is_dark_mode=hero_bg.get("type") == "photograph" or (
                isinstance(analysis.get("typography", {}), dict) and
                analysis.get("typography", {}).get("text_is_white_on_dark", False)
            ),
            is_responsive=True,
            components_detected=components,
            interactions_detected=all_ints,
            content_sections=[c.get("name","") for c in (comps_raw if isinstance(comps_raw,list) else [])],
            target_audience=analysis.get("site_description", ""),
            primary_cta=vt.get("cta_primary", ""),
        )

        return ImagePromptResponse(
            analysis=visual,
            generated_prompt=prompt_data.get("generated_prompt", ""),
            token_estimate=prompt_data.get("token_estimate", 400),
            framework_used=framework,
            prompt_type=prompt_type,
            key_features=prompt_data.get("key_features", []),
            build_complexity=prompt_data.get("build_complexity", "Moderate (4-8 hrs)"),
            tips=prompt_data.get("tips", []),
        ).model_dump()