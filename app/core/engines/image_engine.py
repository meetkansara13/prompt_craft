"""
app/core/engines/image_engine.py  —  PromptCraft Pro v4 PEAK ACCURACY
======================================================================
The ONLY job of this engine: generate a prompt so accurate that pasting
it into ANY AI produces the correct UI in ONE shot. No second attempt.

Root cause of failure (fixed here):
  - Stage 1 was falling back to page-type defaults (#3B82F6 blue) instead
    of reading actual colors from the image.
  - Stage 2 was generating generic "tech startup" prompts regardless of
    what the image actually showed.

Fixes:
  1. Stage 1: Forces hex extraction from visible pixels. "NEVER use
     default colors. NEVER use #3B82F6 unless it is literally in the image."
  2. Stage 1: Describes WHAT IS VISIBLE — actual text, actual images,
     actual color regions — not inferred categories.
  3. Stage 2: Builds prompt from the ACTUAL analysis, not from templates.
     Every sentence references something from the extracted data.
  4. Both stages: Anti-hallucination rules are the first thing the model reads.
"""

from app.utils.logger import get_logger

logger = get_logger(__name__)

FRAMEWORK_STAGE2 = {
    "react": {
        "name": "React 18 with functional components and hooks",
        "styling": "CSS Modules. All colors as CSS custom properties in :root.",
        "components": "PascalCase names. PropTypes or TypeScript interfaces.",
        "interactions": "CSS :hover/:focus-visible for states. Framer Motion for animations.",
        "tools": "Vite + React 18 + TypeScript + CSS Modules.",
    },
    "nextjs": {
        "name": "Next.js 14 App Router with Server and Client Components",
        "styling": "Tailwind CSS v3. All detected colors in tailwind.config.ts extends.colors.",
        "components": "Server Components by default. 'use client' only for interactive parts.",
        "interactions": "Tailwind hover:/focus: utilities. transition-all duration-200.",
        "tools": "Next.js 14 + TypeScript + Tailwind CSS 3 + shadcn/ui base.",
    },
    "vue": {
        "name": "Vue 3 with Composition API and <script setup>",
        "styling": "Scoped CSS in SFCs. CSS custom properties for design tokens.",
        "components": "defineProps<T>() and defineEmits<T>() on every component.",
        "interactions": "Vue <Transition> for animations. @mouseenter/@mouseleave for hover.",
        "tools": "Vite + Vue 3 + TypeScript + Pinia + Vue Router 4.",
    },
    "html": {
        "name": "Semantic HTML5 with Vanilla CSS and Vanilla JavaScript",
        "styling": "CSS custom properties in :root. BEM class naming. Mobile-first.",
        "components": "Semantic elements: <header> <nav> <main> <section> <article> <footer>.",
        "interactions": "CSS transitions on all interactive elements. IntersectionObserver for scroll.",
        "tools": "No build step. Pure HTML/CSS/JS.",
    },
    "tailwind": {
        "name": "HTML with Tailwind CSS v3 and Alpine.js",
        "styling": "Tailwind utilities only. All detected colors in tailwind.config.js.",
        "components": "Alpine.js x-data for state. x-show/x-bind/x-on for interactions.",
        "interactions": "hover: focus: transition-all duration-200 ease-in-out.",
        "tools": "Tailwind CLI or Vite. Alpine.js CDN.",
    },
    "flutter": {
        "name": "Flutter 3 with Dart — Material 3 and Custom ThemeData",
        "styling": "ColorScheme with Color(0xFFXXXXXX) constants. TextTheme hierarchy.",
        "components": "StatelessWidget for static. StatefulWidget for interactive. PascalCase.",
        "interactions": "InkWell ripple. AnimatedContainer for hover. AnimatedOpacity for focus.",
        "tools": "Flutter 3.x + Dart 3 + flutter_riverpod + Material 3.",
    },
}

PROMPT_TYPE_GOAL = {
    "build":    "Build this UI from absolute scratch so it is pixel-for-pixel identical to the original.",
    "improve":  "Analyze this UI critically and list specific improvements with severity and exact fixes.",
    "describe": "Write a comprehensive plain-English description of this UI for a developer brief.",
}


class ImageEngine:

    # ══════════════════════════════════════════════════════════════════════
    # STAGE 1 — The most important prompt in this entire codebase.
    # If Stage 1 fails to extract real colors/components, the final prompt
    # will be wrong. Every word here is chosen to prevent hallucination.
    # ══════════════════════════════════════════════════════════════════════

    STAGE1_SYSTEM = """\
You are a pixel-level UI analyst. Your ONLY job is to extract what is LITERALLY
VISIBLE in this image — colors, text, components, layout. Not what you think
a similar page usually looks like. What is ACTUALLY IN THIS IMAGE.

═══════════════════════════════════════════════════════════════
ANTI-HALLUCINATION RULES — READ THESE FIRST
═══════════════════════════════════════════════════════════════
1. COLORS: Sample the actual hex value of each color region you see.
   NEVER use default/generic colors like #3B82F6, #6B7280, #E5E7EB
   unless those exact colors are literally visible in the image.
   If you see dark green → extract that dark green's hex.
   If you see teal water → extract that teal's hex.
   If you see orange buttons → extract that orange's hex.

2. PAGE TYPE: Look at what is IN the image, not what category it might be.
   If you see a travel photo, mountains, ocean → it's a travel/tourism site.
   If you see code, dashboards, charts → it's a SaaS/tech site.
   If you see products, prices → it's e-commerce.
   NEVER default to "landing_page" unless you genuinely cannot tell.

3. TEXT: Read and report the EXACT visible text in the image.
   Hero headline, navigation links, button labels, taglines — copy them exactly.
   If text is unreadable, say "unreadable" — do not invent text.

4. IMAGES: If the background is a photograph, describe what is IN the photo:
   "full-bleed photograph of tropical ocean with limestone cliffs and woman
    in straw hat in foreground" — be this specific.

5. COMPONENTS: Name what you ACTUALLY SEE:
   "utility bar with phone number, email, social icons, orange pill button"
   NOT "header navigation bar" (generic).

6. IF UNSURE: Give your best estimate and note it as "estimated:".
   NEVER fall back to generic defaults.
═══════════════════════════════════════════════════════════════

APPROACH — do this in your head before writing JSON:
Step 1: What is the dominant background? (photo, solid color, gradient?) → extract hex
Step 2: What are the 3 most prominent colors? → sample each hex
Step 3: What text is visible? → copy it exactly
Step 4: What sections/regions exist top to bottom?
Step 5: What interactive elements are visible?
Then write the JSON.

RESPOND ONLY WITH VALID JSON. No markdown fences. No text outside JSON.

{
  "page_type": "travel | e-commerce | saas | blog | portfolio | dashboard | restaurant | real_estate | education | healthcare | other — describe specifically",
  "site_description": "2-3 sentences describing what this site IS based on what you see: industry, purpose, visual style, target audience",
  "hero_background": {
    "type": "photograph | solid_color | gradient | video_thumbnail | illustration",
    "description": "if photograph: describe what is in the photo in detail. if color/gradient: describe the colors",
    "dominant_hex": "#XXXXXX — the most prominent background color you can sample"
  },
  "visible_text": {
    "page_title": "exact text of the largest heading visible",
    "subtitle": "exact text of any subtitle",
    "script_text": "exact text of any script/cursive text",
    "cta_primary": "exact label of primary action button",
    "cta_secondary": "exact label of secondary button if present",
    "nav_links": ["exact nav link labels as visible"],
    "other_text": ["any other significant visible text"]
  },
  "colors": {
    "instructions": "Sample these from the ACTUAL IMAGE. No defaults.",
    "background_primary": {"hex": "#XXXXXX", "where": "describe exactly where this color appears"},
    "background_secondary": {"hex": "#XXXXXX", "where": "second most prominent bg color"},
    "primary_action": {"hex": "#XXXXXX", "where": "buttons, links, accents"},
    "secondary_action": {"hex": "#XXXXXX", "where": "secondary buttons or elements"},
    "text_on_dark": {"hex": "#XXXXXX", "where": "text color on dark backgrounds"},
    "text_on_light": {"hex": "#XXXXXX", "where": "text color on light backgrounds"},
    "nav_background": {"hex": "#XXXXXX", "where": "navigation bar background"},
    "accent": {"hex": "#XXXXXX", "where": "highlight color, underlines, decorative elements"},
    "additional": [{"hex": "#XXXXXX", "where": "describe"}]
  },
  "typography": {
    "heading_style": "serif | sans-serif | display | script — describe the ACTUAL font style you see",
    "heading_weight": "light | regular | bold | black/heavy",
    "has_script_font": true,
    "script_font_description": "describe the cursive/script text style if present",
    "body_style": "sans-serif | serif",
    "estimated_h1_size": "e.g. very large (80-120px) | large (48-72px) | medium (32-48px)",
    "text_is_white_on_dark": true
  },
  "layout": {
    "structure": "full_bleed_hero | split | sidebar | grid | single_column",
    "has_utility_bar": true,
    "utility_bar_content": "describe what is in the utility bar if present",
    "nav_style": "transparent_over_hero | solid | sticky | dark | light",
    "nav_position": "top_fixed | top_static | sidebar | none",
    "hero_text_position": "center | left | right | bottom_left",
    "content_max_width": "estimated max width e.g. 1280px"
  },
  "components": [
    {
      "name": "precise descriptive name — e.g. 'utility bar with contact info and book now button'",
      "count": 1,
      "description": "detailed visual description: colors, size, content, position",
      "key_styles": "border-radius, shadows, padding estimates"
    }
  ],
  "interactions": {
    "hover_effects": ["describe each visible hover state"],
    "animations": ["describe visible animations"],
    "scroll_behaviors": ["describe scroll-triggered behaviors"],
    "special_effects": ["overlay on hero image", "parallax", "etc"]
  },
  "design_style": "describe the overall visual style in 1-2 sentences: dramatic, minimal, luxury, adventure, corporate, playful etc",
  "build_complexity": "Simple (1-2 hrs) | Moderate (4-8 hrs) | Complex (1-2 days) | Advanced (3-5 days)"
}"""

    STAGE1_USER = """\
Analyze this UI screenshot. Extract what is LITERALLY VISIBLE.

CRITICAL — before writing any JSON:
1. Look at the BACKGROUND — is it a photograph? What is in it? What color is it?
2. Read the EXACT TEXT you can see — headlines, nav links, button labels
3. SAMPLE the actual colors — dark greens, teals, oranges, whatever is there
4. Name the components by what they ACTUALLY ARE, not generic labels

ANTI-DEFAULTS CHECK before submitting:
- Did you use any of these? #3B82F6 #6B7280 #E5E7EB #F8FAFC #111827
  If yes and that color is NOT literally in the image → REPLACE with what you actually see.
- Did you write "landing_page" as page_type? Is it ACTUALLY a travel/e-commerce/portfolio/etc site?
  If yes → REPLACE with the accurate type.
- Did you copy exact text from the image? → If not, go back and read it.

Return only valid JSON.\
"""

    # ══════════════════════════════════════════════════════════════════════
    # STAGE 2 — Build the final prompt from REAL extracted data
    # ══════════════════════════════════════════════════════════════════════

    def build_stage2_system(self, framework: str, prompt_type: str) -> str:
        fw = FRAMEWORK_STAGE2.get(framework, FRAMEWORK_STAGE2["html"])
        goal = PROMPT_TYPE_GOAL.get(prompt_type, PROMPT_TYPE_GOAL["build"])

        return f"""\
You are PromptCraft Pro — the world's most accurate UI prompt engineer.
You receive a JSON analysis of a UI screenshot and write a prompt so precise
that any AI can reproduce the UI in ONE SHOT with no follow-up needed.

FRAMEWORK: {fw["name"]}
STYLING: {fw["styling"]}
COMPONENTS: {fw["components"]}
INTERACTIONS: {fw["interactions"]}
TOOLS: {fw["tools"]}

GOAL: {goal}

══════════════════════════════════════════════════════════════
ACCURACY RULES FOR THE GENERATED PROMPT
══════════════════════════════════════════════════════════════
1. COLORS: Every hex color from the analysis MUST appear in the prompt
   as a named design token. NO substitutions. If analysis says #1A3A2E →
   the prompt must say "--color-nav-bg: #1A3A2E" or equivalent.

2. BACKGROUND: If the hero has a photograph, you MUST do two things in the prompt:
   a) Describe the photograph in precise detail: subject, colors, mood, composition.
   b) Provide a REAL Unsplash image URL that matches the photo description.
      Use this format: https://images.unsplash.com/photo-[ID]?w=1600&q=80
      Match the subject accurately:
      - Desert/camel/sand dunes → photo-1509316785289-025f5b846b35 (camel desert)
      - Tropical ocean/cliffs → photo-1506905925346-21bda4d32df4 (ocean cliffs)
      - Travel/adventure → photo-1488646953014-85cb44e25828 (adventure travel)
      - Beach/coastal → photo-1507525428034-b723cf961d3e (beach sunset)
      - Palace/heritage → photo-1477959858617-67f85cf4f1df (palace building)
      - Forest/mountain → photo-1464822759023-fed622ff2c3b (mountain forest)
      - City/urban → photo-1477959858617-67f85cf4f1df (city skyline)
      - Winter/snow/white → photo-1547036967-23d11aacaee0 (snowy landscape)
      - Festival/cultural → photo-1540575467063-178a50c2df87 (cultural festival)
      ALWAYS include: <img src="[URL]" alt="description" style="width:100%;height:100%;object-fit:cover"/>
      The developer must use a REAL photo, not CSS gradients or placeholder colors.

3. TEXT: Include EXACT text from visible_text. The prompt must say:
   'The hero headline reads "Adventure Travel" in bold uppercase white'
   NOT 'add a hero headline'.

4. COMPONENTS: Every component from the analysis must have a named section
   in the prompt with exact visual specs.

5. SPECIFICITY — these phrases are BANNED in your output:
   "appropriate colors" → specify the hex
   "modern design" → describe the actual style
   "clean layout" → describe the actual layout
   "suitable font" → specify the font style
   "responsive design" → specify the breakpoints
   "add relevant content" → specify the actual content from the image

6. LENGTH: The prompt must be minimum 500 words. A short prompt = vague result.

7. STRUCTURE: Use this exact format:
   [ROLE] — who the developer is
   [WHAT YOU ARE BUILDING] — describe the site from the analysis
   [DESIGN TOKENS] — every color, every typography value
   [HERO / BACKGROUND] — exact description of the hero section
   [NAVIGATION] — exact nav spec
   [COMPONENTS] — each component with full visual spec
   [INTERACTIONS] — every hover, animation, scroll behavior
   [CONSTRAINTS] — hard rules with specific values
   [VERIFICATION] — checklist
══════════════════════════════════════════════════════════════

RESPOND ONLY WITH VALID JSON:
{{
  "generated_prompt": "The complete prompt — minimum 500 words. References actual colors, actual text, actual components from the analysis. Never generic.",
  "token_estimate": number,
  "key_features": [
    "specific feature referencing actual visual elements from the analysis",
    "e.g. Full-bleed hero photograph of tropical ocean with limestone cliffs",
    "e.g. Utility bar with phone, email, social icons, and orange Book Now button",
    "e.g. Script font headline: Discover the World in white Dancing Script",
    "e.g. Navigation: transparent over hero, dark green brand, 6 nav links"
  ],
  "build_complexity": "from analysis",
  "tips": [
    "Specific tip 1 for this exact UI type and framework",
    "Specific tip 2",
    "Specific tip 3"
  ],
  "color_tokens": {{
    "primary": "hex from analysis — NO defaults",
    "secondary": "hex from analysis",
    "accent": "hex from analysis",
    "background": "hex from analysis",
    "text_primary": "hex from analysis",
    "nav_bg": "hex from analysis"
  }}
}}\
"""

    def build_stage2_user(self, analysis_json: str, framework: str, prompt_type: str) -> str:
        return f"""\
VISUAL ANALYSIS FROM STAGE 1:
{analysis_json}

Generate a {prompt_type.upper()} prompt for {framework.upper()}.

MANDATORY CHECKLIST — verify every item before returning:
1. Did I use the EXACT hex values from analysis.colors? (not defaults) ✓
2. Did I include the EXACT text from analysis.visible_text? ✓
3. Did I describe the hero background from analysis.hero_background? ✓
4. Did I spec every component from analysis.components? ✓
5. Did I include all interactions from analysis.interactions? ✓
6. Is generated_prompt at least 500 words? ✓
7. Are all 6 color_tokens filled with hex values from the analysis? ✓
8. Are key_features specific to THIS image (not generic)? ✓

If any item is NO — fix it before returning.
Return only valid JSON.\
"""

    def get_stage1_prompts(self) -> tuple[str, str]:
        return self.STAGE1_SYSTEM, self.STAGE1_USER

    def get_stage2_prompts(self, analysis_json: str, framework: str, prompt_type: str) -> tuple[str, str]:
        return (
            self.build_stage2_system(framework, prompt_type),
            self.build_stage2_user(analysis_json, framework, prompt_type),
        )