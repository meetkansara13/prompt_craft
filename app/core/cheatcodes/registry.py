"""
app/core/cheatcodes/registry.py
=================================
All model-specific cheat codes as structured Python objects.
These are injected into the AI system prompt at generation time.
Having them here as Python data means they can be:
  - tested independently
  - versioned per model
  - filtered by technique selection
  - updated without touching prompt strings
"""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class CheatCode:
    key: str
    model: str          # claude | chatgpt | gpt5 | gemini | deepseek | grok | universal
    title: str
    description: str
    example: str = ""
    token_impact: str = ""   # e.g. "saves ~20 tokens per occurrence"


# ── CLAUDE ────────────────────────────────────────────────────────────────────
CLAUDE_CODES: list[CheatCode] = [
    CheatCode(
        key="claude_xml",
        model="claude",
        title="XML Tag Structure",
        description="Wrap every section in XML tags: <role>, <context>, <task>, <constraints>, <format>, <examples>, <verification>. Claude 4.6 parses these with highest fidelity — fewer misinterpretations than prose.",
        example="<task>Write a product description for...</task>",
    ),
    CheatCode(
        key="claude_no_prefill",
        model="claude",
        title="Prefill Deprecated — Use Explicit Format Instruction",
        description="Prefilling the last assistant turn is DEPRECATED in Claude 4.6. Instead: end your prompt with 'Output only valid JSON with no preamble.' or 'Begin your response with: {'.",
        example="Output only valid JSON with no preamble.",
    ),
    CheatCode(
        key="claude_no_think",
        model="claude",
        title="Avoid the Word 'Think'",
        description="Use 'reason through', 'evaluate', or 'work through' instead of 'think' to avoid accidentally triggering extended-thinking mode on tasks that don't need it.",
        example="Reason through this step by step.",
    ),
    CheatCode(
        key="claude_effort",
        model="claude",
        title="Effort Control",
        description="Claude 4.6 defaults to HIGH effort mode and often over-generates. For simple tasks explicitly say 'Use concise effort. Max 400 words.' to prevent bloated responses.",
        example="Use concise effort. Max 400 words.",
        token_impact="Can reduce output by 30-60% on simple tasks",
    ),
    CheatCode(
        key="claude_cache",
        model="claude",
        title="Prompt Caching — 75% Cost Reduction",
        description="Put static system instructions FIRST (they get cached). Put dynamic user content LAST. Claude caches prompts over 1024 tokens — repeat calls cost 75% less.",
        example="cache_control: {type: 'ephemeral'}",
        token_impact="75% cost reduction on cached content",
    ),
    CheatCode(
        key="claude_principles",
        model="claude",
        title="Principle-Based Constraints",
        description="Claude responds better to principle-based constraints ('Prioritize accuracy over completeness') than exhaustive rule lists. 1 principle > 5 rules.",
    ),
]

# ── CHATGPT / GPT-4o ──────────────────────────────────────────────────────────
CHATGPT_CODES: list[CheatCode] = [
    CheatCode(
        key="gpt_system_user",
        model="chatgpt",
        title="System / User Role Separation",
        description="Always separate SYSTEM (persona + standing rules) from USER (task). Never mix them. GPT-4o gives strongest weight to instructions in the system role.",
    ),
    CheatCode(
        key="gpt_cot",
        model="chatgpt",
        title="Chain-of-Thought Trigger",
        description="'Let's think step by step.' reliably triggers CoT in GPT-4o. Place it at the END of the user message for best effect.",
        example="Let's think step by step.",
    ),
    CheatCode(
        key="gpt_json",
        model="chatgpt",
        title="JSON Mode",
        description="Set response_format: {type: 'json_object'} in API call AND mention JSON in the system prompt. Both are required — one alone is unreliable.",
        example='{"response_format": {"type": "json_object"}}',
        token_impact="Eliminates format instruction tokens",
    ),
    CheatCode(
        key="gpt_fewshot",
        model="chatgpt",
        title="Few-Shot Quality Over Quantity",
        description="2-3 high-quality INPUT→OUTPUT examples outperform 10 mediocre ones and cost fewer tokens. Always format examples identically to desired output.",
    ),
]

# ── GPT-5 ─────────────────────────────────────────────────────────────────────
GPT5_CODES: list[CheatCode] = [
    CheatCode(
        key="gpt5_explicit",
        model="gpt5",
        title="Explicit Over Implied",
        description="GPT-5 has exceptional instruction following. State requirements explicitly — implications and hints are less reliable than clear statements.",
    ),
    CheatCode(
        key="gpt5_no_preamble",
        model="gpt5",
        title="No Persona Preamble Needed",
        description="GPT-5 doesn't need verbose role-setting. 'You are a helpful expert in X' is enough. Task-first prompting outperforms lengthy character-building.",
        token_impact="Saves 50-100 tokens on preamble",
    ),
    CheatCode(
        key="gpt5_cot",
        model="gpt5",
        title="Reasoning Trigger",
        description="'Reason through this carefully before answering.' works better than 'Let's think step by step' for GPT-5's reasoning style.",
        example="Reason through this carefully before answering.",
    ),
]

# ── GEMINI ────────────────────────────────────────────────────────────────────
GEMINI_CODES: list[CheatCode] = [
    CheatCode(
        key="gemini_ptcf",
        model="gemini",
        title="PTCF Is Native",
        description="Persona · Task · Context · Format is native to Gemini 2.5 Pro's training. Using this structure produces reliably better results than any other framework.",
    ),
    CheatCode(
        key="gemini_schema",
        model="gemini",
        title="responseSchema for JSON",
        description="Use responseSchema in the API call instead of asking for JSON in the prompt. Gemini enforces it natively — zero format instructions needed.",
        example="responseSchema: {type: 'object', properties: {...}}",
        token_impact="Eliminates all format instruction tokens",
    ),
    CheatCode(
        key="gemini_grounding",
        model="gemini",
        title="Anti-Hallucination Grounding",
        description="End factual prompts with: 'Base your answer only on the provided context. If you are unsure, say so explicitly. Do not hallucinate.'",
        example="Base your answer only on provided context. Do not hallucinate.",
    ),
    CheatCode(
        key="gemini_url",
        model="gemini",
        title="URL Context — Save Thousands of Tokens",
        description="Instead of pasting full documents, pass URLs. Gemini 2.5 Pro fetches and reads them natively. Can save thousands of tokens for long-context tasks.",
        token_impact="Saves thousands of tokens for document tasks",
    ),
    CheatCode(
        key="gemini_concise",
        model="gemini",
        title="Be Direct — Less Is More",
        description="Gemini 2.5 Pro prefers direct, concise instructions. Over-engineered prompts with excessive preamble actually reduce output quality.",
    ),
]

# ── DEEPSEEK ──────────────────────────────────────────────────────────────────
DEEPSEEK_CODES: list[CheatCode] = [
    CheatCode(
        key="deepseek_r1_reasoning",
        model="deepseek",
        title="R1 Built-in Reasoning — Don't Add CoT",
        description="DeepSeek-R1 has extended thinking built in. Do NOT add 'think step by step' instructions — they waste tokens on a model that already reasons internally.",
        token_impact="Avoids 10-20 wasted instruction tokens per call",
    ),
    CheatCode(
        key="deepseek_task_first",
        model="deepseek",
        title="Task-First, No Theatrics",
        description="DeepSeek performs best with direct, technical, task-focused instructions. Skip lengthy persona setups. Lead with the task.",
    ),
    CheatCode(
        key="deepseek_code",
        model="deepseek",
        title="Code: Specify Everything",
        description="For code tasks: always specify language, version, framework, coding style, and whether tests are needed. DeepSeek takes these constraints literally.",
        example="Python 3.11, FastAPI, type hints required, pytest tests included.",
    ),
]

# ── GROK ──────────────────────────────────────────────────────────────────────
GROK_CODES: list[CheatCode] = [
    CheatCode(
        key="grok_search",
        model="grok",
        title="Invoke Real-Time Search",
        description="Grok 3 has live web search. For any task requiring current data, explicitly say: 'Search for the latest information on X before answering.'",
        example="Search for the latest information on X before answering.",
    ),
    CheatCode(
        key="grok_personality",
        model="grok",
        title="Personality-Driven Framing Works",
        description="Unlike Claude, Grok responds well to personality-driven prompts. 'Be direct and witty where appropriate' genuinely improves output quality and tone.",
    ),
    CheatCode(
        key="grok_direct",
        model="grok",
        title="Direct and Punchy",
        description="Grok responds best to short, direct, punchy instructions. Long-winded setups reduce effectiveness. Get to the point fast.",
    ),
]

# ── UNIVERSAL ─────────────────────────────────────────────────────────────────
UNIVERSAL_CODES: list[CheatCode] = [
    CheatCode(
        key="chain_of_draft",
        model="universal",
        title="Chain-of-Draft (80% Fewer Reasoning Tokens)",
        description="Replace 'Think step by step' with 'Draft your key reasoning steps in minimal notes, then give the final answer.' Same quality. 80% fewer reasoning tokens.",
        example="Draft key steps briefly, then give your final answer.",
        token_impact="80% reduction in reasoning tokens",
    ),
    CheatCode(
        key="token_budget",
        model="universal",
        title="Token Budget Declaration",
        description="Declare a token budget explicitly: 'Max 400 words. Use Chain-of-Draft reasoning.' This improves compliance AND reduces output tokens. A cheat code that works on all models.",
        example="Max 400 words. Use Chain-of-Draft reasoning.",
        token_impact="30-60% reduction depending on task",
    ),
    CheatCode(
        key="primacy_recency",
        model="universal",
        title="Primacy + Recency Rule",
        description="State the single most important requirement FIRST and LAST. All LLMs attend most strongly to content at the very start and very end. The middle is lossy.",
    ),
    CheatCode(
        key="remove_filler",
        model="universal",
        title="Remove All Filler Phrases",
        description="'Please make sure to', 'It is important that', 'Try to ensure', 'Please' — each adds 5-15 tokens and DILUTES attention on actual rules. Remove every one.",
        token_impact="5-15 tokens saved per occurrence",
    ),
    CheatCode(
        key="one_rule_once",
        model="universal",
        title="One Rule, Once",
        description="Restating the same constraint 2-3 ways is the #1 token waste in production prompts. State each rule ONCE, precisely. Trust the model to follow it.",
    ),
    CheatCode(
        key="positive_reframe",
        model="universal",
        title="Positive Reframing",
        description="'Don't write casually' → 'Write in a professional, authoritative tone.' Positive instructions cost fewer tokens and are followed more reliably than negative ones.",
    ),
]

# ── REGISTRY ──────────────────────────────────────────────────────────────────
ALL_CODES: list[CheatCode] = (
    CLAUDE_CODES + CHATGPT_CODES + GPT5_CODES +
    GEMINI_CODES + DEEPSEEK_CODES + GROK_CODES + UNIVERSAL_CODES
)

CHEATCODE_REGISTRY: dict[str, CheatCode] = {c.key: c for c in ALL_CODES}

BY_MODEL: dict[str, list[CheatCode]] = {
    "claude":    CLAUDE_CODES,
    "chatgpt":   CHATGPT_CODES,
    "gpt5":      GPT5_CODES,
    "gemini":    GEMINI_CODES,
    "deepseek":  DEEPSEEK_CODES,
    "grok":      GROK_CODES,
    "universal": UNIVERSAL_CODES,
}


def get_codes_for_model(model: str) -> list[CheatCode]:
    """Return model-specific codes + universal codes."""
    specific  = BY_MODEL.get(model, [])
    universal = BY_MODEL.get("universal", [])
    return specific + universal


def get_selected_codes(keys: list[str]) -> list[CheatCode]:
    """Return CheatCode objects for a list of selected keys."""
    return [CHEATCODE_REGISTRY[k] for k in keys if k in CHEATCODE_REGISTRY]


def format_codes_for_prompt(model: str) -> str:
    """Format all codes for a model into a prompt-ready string block."""
    codes = get_codes_for_model(model)
    lines = []
    for code in codes:
        lines.append(f"• {code.title}: {code.description}")
        if code.example:
            lines.append(f"  Example: {code.example}")
        if code.token_impact:
            lines.append(f"  Token impact: {code.token_impact}")
    return "\n".join(lines)
