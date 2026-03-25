"""
app/core/engines/token_engine.py
==================================
Builds system prompts for the Token Optimizer.
Pure Python — no Flask, no HTTP.
"""

from app.utils.logger import get_logger

logger = get_logger(__name__)


class TokenEngine:
    """
    Builds system prompts and user messages for the Token Optimizer.
    The logic for WHAT makes a good token-optimized prompt lives here
    as Python data — not buried in a raw string in a route handler.
    """

    # ── Token science knowledge base ─────────────────────────────────────────
    TOKEN_SCIENCE = """
TOKEN OPTIMIZATION RESEARCH FINDINGS (2025-2026):

PROVEN TECHNIQUES:
• Chain-of-Draft (CoD): Replace "think step by step" with "draft key steps briefly, then give final answer"
  — Achieves 80-90% fewer reasoning tokens with equal or better accuracy vs Chain-of-Thought
  — Impact: 80-90% reduction in reasoning token usage

• Lost-in-the-Middle Problem: LLMs attend LEAST to content in the middle of long prompts
  — Critical instructions must go at the START and END
  — Impact: Dramatically improves compliance without adding tokens

• Redundant Politeness Removal: "Please", "Thank you", "I would like you to", "Could you please"
  — These add 20-50 tokens per prompt with zero benefit to output quality
  — Impact: 5-15 tokens saved per occurrence

• Positive Reframing: "Don't write casually" → "Write in a professional tone"
  — Positive instructions are shorter AND followed more reliably
  — Impact: 5-10 tokens saved, better compliance

• Prompt Caching (Claude 4.6, GPT-4o): Static prefix content costs 75% less on repeat calls
  — Put stable system instructions FIRST, dynamic user content LAST
  — Impact: 75% cost reduction on cached content

• Structure Packing: "Item: value" pairs and bullet points are 20-30% more token-efficient than prose
  — Impact: 20-30% reduction on instruction blocks

• Few-Shot Quality Over Quantity: 2 perfect examples > 10 mediocre ones at half the token cost
  — Impact: Up to 50% reduction in example tokens

• Hedge Language Removal: "try to", "please ensure", "make sure to", "it is important that"
  — Each occurrence adds 5-15 tokens and dilutes model attention on actual rules
  — Impact: 5-15 tokens per occurrence

• One Rule Once: Restating the same constraint 2-3 ways is the most common production waste
  — State each rule ONCE, precisely. Trust the model.
  — Impact: 30-100 tokens saved in constraint-heavy prompts

• Token Budget Declaration: Declaring "Max 400 words. Use Chain-of-Draft." is itself a cheat code
  — Explicitly managing tokens improves output quality AND reduces generation cost
  — Impact: 30-60% output reduction on verbose tasks

• Verbose Role-Setting Compression: "You are a helpful, friendly, knowledgeable assistant that always..." 
  — Can be compressed to "Expert [domain] assistant." with equal or better results
  — Impact: 50-100 tokens saved

MODEL-SPECIFIC TOKEN TIPS:
• Claude 4.6: Prefill deprecated. Use explicit format instruction. Add effort control for simple tasks.
• GPT-4o: System role content is cheaper. Move stable instructions there.
• GPT-5: No padding needed. Strong instruction following with minimal tokens.
• Gemini 2.5 Pro: responseSchema in API eliminates all format instruction tokens.
• DeepSeek-R1: Has built-in reasoning. Never add CoT instructions — pure token waste.
• Grok 3: Direct and punchy beats elaborate setup."""

    OUTPUT_SCHEMA = '''
RESPOND ONLY WITH VALID JSON. No markdown fences, no preamble.

Required JSON schema:
{
  "analysis": {
    "original_tokens": number,
    "waste_pct": number,
    "token_breakdown": [
      {"category": "Task Instructions",    "tokens": number, "pct": number, "color": "teal"},
      {"category": "Redundant Politeness", "tokens": number, "pct": number, "color": "rose"},
      {"category": "Role/Context",         "tokens": number, "pct": number, "color": "gold"},
      {"category": "Constraints/Rules",    "tokens": number, "pct": number, "color": "violet"},
      {"category": "Filler Phrases",       "tokens": number, "pct": number, "color": "rose"},
      {"category": "Examples/Format",      "tokens": number, "pct": number, "color": "teal"}
    ],
    "issues": [
      {"severity": "high|medium|low|info", "icon": "emoji", "title": "Issue name", "desc": "What it is and why it wastes tokens", "save": "~X tokens saved by fixing this"}
    ]
  },
  "versions": {
    "balanced": {
      "prompt": "30-45% fewer tokens, all meaning preserved. Natural language, still readable.",
      "tokens": number, "pct": number,
      "techniques": ["Semantic Trim", "Filler Removal", "Negative Reframe"]
    },
    "aggressive": {
      "prompt": "50-70% fewer tokens. Telegraphic but complete. May use bullets and colons.",
      "tokens": number, "pct": number,
      "techniques": ["All above + Structure Pack + Chain-of-Draft + Batch Pack"]
    },
    "ultra": {
      "prompt": "70-85% reduction. Near-code density. Every word earns its place.",
      "tokens": number, "pct": number,
      "techniques": ["All techniques + Symbolic compression + Context abbreviation"]
    }
  },
  "quality": {
    "semantic_retention": number,
    "intent_clarity": number,
    "readability": number,
    "accuracy_risk": number
  },
  "savings": {
    "tokens_saved": number,
    "cost_pct": number,
    "speed_pct": number,
    "example": "e.g. $8.40 → $4.90 at 100k requests/month on GPT-4o"
  },
  "techniques_applied": [
    {"icon": "emoji", "name": "Technique Name", "desc": "Specifically what was done in this prompt", "saved": number}
  ],
  "model_tips": {
    "claude":    [{"icon":"🔖","title":"tip","desc":"description","code":"code or null"}],
    "chatgpt":   [{"icon":"🎭","title":"tip","desc":"description","code":null}],
    "gemini":    [{"icon":"📐","title":"tip","desc":"description","code":null}],
    "deepseek":  [{"icon":"🧠","title":"tip","desc":"description","code":null}],
    "universal": [{"icon":"✂️","title":"tip","desc":"description","code":null}]
  }
}'''

    def build_system_prompt(self) -> str:
        """Assemble the token optimizer system prompt."""
        return (
            "You are TokenLens Pro — the world's most advanced AI prompt token optimizer. "
            "You have deep expertise in token economics and compression techniques based on "
            "2025-2026 research.\n\n"
            + self.TOKEN_SCIENCE
            + "\n\n"
            + self.OUTPUT_SCHEMA
        )

    def build_user_message(
        self,
        prompt: str,
        target_model: str,
        level: str,
        sensitivity: str,
        techniques: list[str],
        original_token_estimate: int,
    ) -> str:
        """Build the user message for optimization."""
        return f"""PROMPT TO OPTIMIZE:
---
{prompt}
---

OPTIMIZATION SETTINGS:
- Target model: {target_model}
- Optimization level: {level}
- Task sensitivity: {sensitivity}
- Techniques enabled: {", ".join(techniques) or "all"}
- Estimated original tokens: ~{original_token_estimate}

Analyze this prompt completely:
1. Find EVERY source of token waste — categorize and quantify each
2. Generate all 3 optimized versions (balanced, aggressive, ultra)
3. Each version must preserve 100% of the semantic intent
4. Provide realistic token estimates (approximately chars/4)
5. Give model-specific tips for further token reduction

The balanced version must work as a drop-in replacement — same meaning, fewer tokens."""

    @staticmethod
    def estimate_tokens(text: str) -> int:
        """Rough token estimate: ~4 characters per token."""
        return max(1, round(len(text.strip()) / 4)) if text else 0
