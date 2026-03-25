"""
app/core/engines/prompt_engine.py
===================================
PromptCraft Pro v4 — Claude-style prompt engine.

Rebuilt with Claude's 8 thinking patterns:
  1. Intent-first       — understand WHAT before HOW
  2. Layered structure  — Context→Task→Details→Examples→Verification
  3. Explicit           — specific numbers not vague words
  4. Show don't tell    — INPUT→OUTPUT examples always
  5. Hard constraints   — rules not suggestions
  6. Self-verification  — checklist the AI runs on itself
  7. Domain expertise   — real expertise per category
  8. Output contract    — exact field types defined

Advanced techniques:
  Tree of Thoughts, Self-Consistency, Reflexion,
  Directional Stimulus, Auto-CoT, Generate Knowledge,
  Meta Prompting, Active Prompting
"""

from app.core.frameworks.registry import get_framework, Framework
from app.core.cheatcodes.registry import format_codes_for_prompt, get_selected_codes
from app.utils.logger import get_logger

logger = get_logger(__name__)


class PromptEngine:

    # ── Claude core identity ──────────────────────────────────────────────
    BASE_IDENTITY = (
        "You are PromptCraft Pro v4 — the world's most advanced prompt engineering AI.\n"
        "You think and respond EXACTLY like Claude (Anthropic) — structured, precise,\n"
        "layered, expert-level. You never produce vague or generic prompts.\n\n"
        "YOUR THINKING STYLE (apply to EVERY prompt you generate):\n"
        "1. INTENT FIRST: Identify real goal, audience, success criteria before writing.\n"
        "2. LAYERED STRUCTURE: Role→Context→Task→Examples→Constraints→Format→Verification.\n"
        "3. EXPLICIT: Never say 'good' or 'appropriate'. Say '150-200 words', '3 bullets'.\n"
        "4. SHOW DON'T TELL: Add concrete INPUT→OUTPUT examples for any complex instruction.\n"
        "5. HARD CONSTRAINTS: 'Do not exceed 200 words' — not 'try to be concise'.\n"
        "6. SELF-VERIFICATION: End every prompt with task-specific checklist AI runs on itself.\n"
        "7. DOMAIN EXPERTISE: Role specifies years, domain, mental models, operating principles.\n"
        "8. OUTPUT CONTRACT: Define every output field — type, constraints, example value."
    )

    # ── Domain expertise per category ────────────────────────────────────
    DOMAIN_EXPERTISE = {
        "writing":   "senior content strategist and copywriter with 12+ years creating high-converting content for global brands. You understand audience psychology, SEO principles, and persuasion frameworks. You prioritize: clarity > impact > brevity.",
        "coding":    "senior software engineer with 10+ years building production systems at scale. You prioritize: security > correctness > performance > readability. You write code that junior developers can maintain and extend.",
        "analysis":  "senior data analyst and research scientist with 10+ years extracting actionable insights from complex datasets. You think in first principles, question assumptions, and always quantify uncertainty.",
        "creative":  "creative director with 15+ years leading award-winning campaigns. You combine strategic thinking with creative execution. You know when to follow conventions and when to deliberately break them.",
        "business":  "seasoned business strategist with 12+ years advising Fortune 500 companies. You think in systems, identify leverage points, and translate complex strategy into clear executable action plans.",
        "education": "curriculum designer and master educator with 10+ years creating learning experiences that achieve measurable outcomes. You apply cognitive load theory, spaced repetition, and active learning principles.",
        "data":      "senior data scientist with 8+ years building ML pipelines and data products. You prioritize reproducibility, statistical rigor, and interpretability over raw model performance.",
        "agentic":   "AI systems architect with deep expertise in multi-step reasoning, tool use, and autonomous agent design. You design systems that fail gracefully, recover intelligently, and explain their decisions.",
        "auto":      "world-class expert in the relevant domain with 10+ years of hands-on experience. You combine deep technical knowledge with clear, precise communication.",
    }

    # ── Advanced techniques ───────────────────────────────────────────────
    ADVANCED_TECHNIQUES = {
        "tot": (
            "TREE OF THOUGHTS: Before generating the final prompt, internally explore "
            "3 different structural approaches. Evaluate each on: completeness, clarity, "
            "and effectiveness. Select the strongest branch. Show reasoning in explanations."
        ),
        "self_consistency": (
            "SELF-CONSISTENCY: Generate the core task instruction 3 different ways. "
            "Check which version is most consistent with the goal and constraints. "
            "Use the most consistent version in the final prompt."
        ),
        "reflexion": (
            "REFLEXION (Self-Critique): After generating, internally check: "
            "(1) Does role have specific domain expertise? "
            "(2) Are all constraints hard rules not suggestions? "
            "(3) Is there at least one INPUT→OUTPUT example? "
            "(4) Does verification checklist match this specific task? "
            "If any answer is NO, rewrite that section before returning."
        ),
        "directional_stimulus": (
            "DIRECTIONAL STIMULUS: Inject domain-specific keywords and concepts "
            "into role and context sections to steer AI toward desired output quality. "
            "These act as cognitive anchors that reduce hallucination."
        ),
        "generate_knowledge": (
            "GENERATE KNOWLEDGE: Before writing main task instructions, generate "
            "the key domain facts, principles, and mental models the AI needs. "
            "Inject these as context to ground the response in accurate knowledge."
        ),
        "meta_prompting": (
            "META PROMPTING: Use abstract structural patterns rather than "
            "content-specific rules. Design the prompt architecture to work across "
            "variations of this task type, not just this specific instance."
        ),
        "auto_cot": (
            "AUTO-CoT: Automatically generate 2 chain-of-thought examples showing "
            "the reasoning process for this task type. Include these as few-shot "
            "examples to anchor the AI's reasoning pattern."
        ),
        "active_prompting": (
            "ACTIVE PROMPTING: Identify the most ambiguous part of the user's goal. "
            "Resolve it with a concrete assumption stated explicitly in context. "
            "Never leave any ambiguity unresolved."
        ),
    }

    # ── JSON output schema ────────────────────────────────────────────────
    OUTPUT_SCHEMA = (
        "RESPOND ONLY WITH VALID JSON. No markdown fences. No preamble. No text outside JSON.\n"
        "Every field required. Empty strings = failure. Generic text = failure.\n\n"
        "{\n"
        '  "analysis": {\n'
        '    "detected_intent": "One precise sentence: what the user actually wants to achieve",\n'
        '    "task_type": "Content Generation | Code | Analysis | Creative | Conversation | Agentic | Data",\n'
        '    "detected_domain": "Specific domain e.g. E-commerce | SaaS | Healthcare | Engineering",\n'
        '    "complexity": "Simple | Moderate | Advanced | Expert",\n'
        '    "key_requirements": ["4-6 specific requirements — each a complete sentence"],\n'
        '    "ambiguities_resolved": ["ambiguity found + assumption made to resolve it"],\n'
        '    "domain_expertise_used": "Which expert persona was selected and why"\n'
        "  },\n"
        '  "quality_score": {\n'
        '    "score": 0-100,\n'
        '    "grade": "Poor | Fair | Good | Excellent | Elite",\n'
        '    "clarity": 0-100, "specificity": 0-100,\n'
        '    "technique_use": 0-100, "completeness": 0-100,\n'
        '    "improvements": ["specific actionable improvement 1", "improvement 2"]\n'
        "  },\n"
        '  "prompt_sections": {\n'
        '    "system_context": "ROLE: specific expert persona, years, domain, mental models, operating principles. Min 4 sentences. Never generic.",\n'
        '    "context_background": "CONTEXT: situation, background, target audience, purpose, success criteria. Min 3 sentences.",\n'
        '    "main_task": "TASK: numbered steps for multi-part tasks. Each step explicit. Include what to include AND exclude.",\n'
        '    "examples_format": "EXAMPLES: 2-3 concrete INPUT→OUTPUT pairs OR filled template. Never abstract descriptions.",\n'
        '    "constraints_rules": "CONSTRAINTS: 6-10 hard rules. Each a firm requirement. Specific numbers not vague words.",\n'
        '    "self_check": "VERIFICATION: 4-6 specific YES/NO questions AI must pass before returning output. Task-specific."\n'
        "  },\n"
        '  "final_prompt": "Complete assembled prompt. Min 250 words. Copy-paste ready. Reads like Claude wrote it.",\n'
        '  "token_optimized_prompt": "Same prompt at 40-60% fewer tokens using Chain-of-Draft. 100% intent preserved.",\n'
        '  "model_variants": {\n'
        '    "claude": "Claude 4.6 with XML tags <role><context><task><examples><constraints><format><verification>. reason-through not think.",\n'
        '    "chatgpt": "GPT-4o with SYSTEM: USER: separation. CoT trigger if reasoning needed.",\n'
        '    "gemini": "Gemini 2.5 Pro in Persona:|Task:|Context:|Format: structure. Direct and concise.",\n'
        '    "gpt5": "GPT-5 clean explicit text. No padding. Strong instruction following.",\n'
        '    "deepseek": "DeepSeek direct technical. No CoT (R1 has built-in reasoning).",\n'
        '    "grok": "Grok 3 direct punchy. Search instruction for real-time data.",\n'
        '    "universal": "Model-agnostic. Clear headers. Primacy/recency applied."\n'
        "  },\n"
        '  "model_tips": {\n'
        '    "claude":    [{"icon":"🏷️","title":"tip","desc":"specific tip for this prompt","code":"example or null"}],\n'
        '    "chatgpt":   [{"icon":"🎭","title":"tip","desc":"specific tip","code":null}],\n'
        '    "gemini":    [{"icon":"📐","title":"tip","desc":"specific tip","code":null}],\n'
        '    "gpt5":      [{"icon":"⚡","title":"tip","desc":"specific tip","code":null}],\n'
        '    "deepseek":  [{"icon":"🧠","title":"tip","desc":"specific tip","code":null}],\n'
        '    "grok":      [{"icon":"🔍","title":"tip","desc":"specific tip","code":null}],\n'
        '    "universal": [{"icon":"✂️","title":"tip","desc":"specific tip","code":null}]\n'
        "  },\n"
        '  "explanations": [\n'
        '    {"icon":"emoji","color":"gold|teal|violet|green","title":"Technique Name","desc":"2-3 sentences: what it does AND why it improves this specific task."},\n'
        '    {"icon":"emoji","color":"teal","title":"Second Technique","desc":"Explanation..."},\n'
        '    {"icon":"emoji","color":"violet","title":"Third Technique","desc":"Explanation..."}\n'
        "  ],\n"
        '  "diagram_data": {\n'
        '    "sections": [\n'
        '      {"id":"role","label":"Role","color":"violet","tokens":45,"summary":"1 sentence summary"},\n'
        '      {"id":"context","label":"Context","color":"gold","tokens":38,"summary":"1 sentence summary"},\n'
        '      {"id":"task","label":"Task","color":"teal","tokens":62,"summary":"1 sentence summary"},\n'
        '      {"id":"examples","label":"Examples","color":"green","tokens":55,"summary":"1 sentence summary"},\n'
        '      {"id":"constraints","label":"Constraints","color":"rose","tokens":41,"summary":"1 sentence summary"},\n'
        '      {"id":"verification","label":"Verification","color":"teal","tokens":28,"summary":"1 sentence summary"}\n'
        "    ],\n"
        '    "total_tokens": 269,\n'
        '    "optimized_tokens": 145,\n'
        '    "techniques_used": ["technique1", "technique2", "technique3"]\n'
        "  }\n"
        "}"
    )

    def build_system_prompt(
        self,
        framework_key: str,
        target_model: str,
        selected_cheat_keys: list,
        selected_techniques: list,
    ) -> str:
        framework = get_framework(framework_key)
        logger.debug("Building system prompt | fw=%s model=%s", framework_key, target_model)
        parts = [
            self.BASE_IDENTITY, "",
            self._framework_section(framework), "",
            self._domain_expertise_section(), "",
            self._cheatcodes_section(target_model, selected_cheat_keys), "",
            self._techniques_section(selected_techniques), "",
            self._accuracy_guarantees(), "",
            self.OUTPUT_SCHEMA,
        ]
        return "\n".join(parts)

    def build_user_message(
        self, goal, model, category, output_format,
        complexity, tones, framework_key, techniques, cheat_codes,
    ) -> str:
        return (
            f"USER GOAL:\n{goal}\n\n"
            f"CONFIGURATION:\n"
            f"- Target model    : {model}\n"
            f"- Task category   : {category}\n"
            f"- Output format   : {output_format}\n"
            f"- Complexity      : {complexity}\n"
            f"- Tone            : {', '.join(tones) or 'professional'}\n"
            f"- Framework       : {framework_key}\n"
            f"- Techniques      : {', '.join(techniques) or 'auto-select best 3'}\n"
            f"- Cheat codes     : {', '.join(cheat_codes) or 'auto-select best'}\n\n"
            "REQUIREMENTS (non-negotiable):\n"
            "1. Apply Claude thinking style — intent first, layered, explicit.\n"
            "2. Role MUST have specific domain + years + mental models.\n"
            "3. Constraints MUST be hard rules — no vague words.\n"
            "4. Examples MUST show concrete INPUT→OUTPUT pairs.\n"
            "5. Verification MUST be specific to THIS task.\n"
            "6. final_prompt MUST be minimum 250 words.\n"
            "7. ALL 7 model_variants MUST be genuinely optimized for each model.\n"
            "8. diagram_data.sections MUST have accurate token estimates.\n"
            "9. Resolve every ambiguity with a stated assumption.\n"
            "10. quality_score must be honest — not always 90+.\n\n"
            "Fill EVERY field. This is a production prompt. Peak quality required."
        )

    def build_refine_system_prompt(self) -> str:
        return (
            f"{self.BASE_IDENTITY}\n\n"
            "REFINEMENT MODE: Apply user feedback precisely. Keep everything that works.\n\n"
            "RULES:\n"
            "1. Apply feedback EXACTLY as described.\n"
            "2. Keep all sections not mentioned in feedback.\n"
            "3. Do not add constraints not requested.\n"
            "4. After applying: run Reflexion check on all 4 quality gates.\n\n"
            "RESPOND ONLY WITH VALID JSON:\n"
            "{\n"
            '  "improved_prompt": "Full improved prompt. Same or greater length than original.",\n'
            '  "token_optimized_prompt": "40-50% fewer tokens. 100% intent preserved.",\n'
            '  "changes_made": ["Specific change + exact reason why"],\n'
            '  "quality_score": {"score":0-100,"grade":"Poor|Fair|Good|Excellent|Elite",\n'
            '    "clarity":0-100,"specificity":0-100,"technique_use":0-100,"completeness":0-100,\n'
            '    "improvements":["remaining improvement"]}\n'
            "}"
        )

    # ── Private builders ──────────────────────────────────────────────────

    def _framework_section(self, framework: Framework) -> str:
        return (
            f"SELECTED FRAMEWORK: {framework.name} ({framework.full_name})\n"
            f"Structure: {' → '.join(framework.components)}\n"
            f"Best for: {framework.best_for}\n"
            f"Description: {framework.description}\n"
            "Apply this framework's EXACT structure. Each component = distinct fully-developed section."
        )

    def _domain_expertise_section(self) -> str:
        lines = ["DOMAIN EXPERTISE TEMPLATES (select best match for the goal):"]
        for domain, expertise in self.DOMAIN_EXPERTISE.items():
            lines.append(f"  [{domain.upper()}]: {expertise}")
        lines.append("\nCustomize the selected template with specifics from the user's goal.")
        lines.append("The role MUST be specific — never 'you are a helpful assistant'.")
        return "\n".join(lines)

    def _cheatcodes_section(self, target_model: str, selected_keys: list) -> str:
        lines = [f"MODEL CHEAT CODES — TARGET: {target_model.upper()}"]
        lines.append(format_codes_for_prompt(target_model))
        if selected_keys:
            selected = get_selected_codes(selected_keys)
            if selected:
                lines.append("\nUSER-SELECTED CODES:")
                for code in selected:
                    lines.append(f"• {code.title}: {code.description}")
                    if code.example:
                        lines.append(f"  Example: {code.example}")
        return "\n".join(lines)

    def _techniques_section(self, techniques: list) -> str:
        if not techniques:
            return "TECHNIQUES: Auto-select the 3 most powerful techniques for this specific goal."

        standard = {
            "cot":         "CHAIN-OF-THOUGHT: Ask AI to reason step by step before final answer.",
            "fewshot":     "FEW-SHOT: Include 2-3 high-quality INPUT→OUTPUT examples. Quality over quantity.",
            "role":        "ROLE ASSIGNMENT: Specific expert persona with domain + years + operating principles.",
            "cod":         "CHAIN-OF-DRAFT: 'Draft key steps briefly, then give final answer.' 80% fewer tokens.",
            "selfcheck":   "SELF-CHECK: 4-6 specific YES/NO verification questions AI must pass before returning.",
            "xml":         "XML TAGS: <role><context><task><examples><constraints><format><verification>",
            "constraints": "EXPLICIT CONSTRAINTS: 6-10 hard rules with specific numbers. No vague words.",
            "negative":    "NEGATIVE EXAMPLE: Show 1 concrete example of what NOT to do.",
            "stepback":    "STEP-BACK: 'Before answering, identify underlying principles for this task type.'",
            "react":       "ReAct: Reason → Act → Observe loops for multi-step agentic tasks.",
            "metacog":     "METACOGNITIVE: Ask AI to rate confidence (1-10) in each key claim.",
            "primacy":     "PRIMACY/RECENCY: Most critical requirement FIRST and LAST in prompt.",
        }

        lines = ["TECHNIQUES TO APPLY:"]
        for t in techniques:
            if t in standard:
                lines.append(f"• {standard[t]}")
            elif t in self.ADVANCED_TECHNIQUES:
                lines.append(f"• {self.ADVANCED_TECHNIQUES[t]}")
        return "\n".join(lines)

    def _accuracy_guarantees(self) -> str:
        return (
            "ACCURACY REQUIREMENTS — non-negotiable:\n"
            "• final_prompt minimum 250 words\n"
            "• Every constraint must be specific: numbers, formats, exact rules\n"
            "• Examples must show concrete INPUT→OUTPUT — never abstract\n"
            "• Role must name specific domain + years + mental models\n"
            "• Verification must be task-specific — not generic 'check your work'\n"
            "• All 7 model_variants genuinely optimized for each model\n"
            "• quality_score must be honest assessment — not always 90+\n"
            "• diagram_data.sections must have realistic token estimates"
        )
