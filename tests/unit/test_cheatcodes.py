"""
tests/unit/test_cheatcodes.py
================================
Unit tests for the CheatCode registry.
"""

import pytest
from app.core.cheatcodes.registry import (
    get_codes_for_model, get_selected_codes,
    format_codes_for_prompt, ALL_CODES, CHEATCODE_REGISTRY,
    BY_MODEL,
)


KNOWN_MODELS = ["claude", "chatgpt", "gpt5", "gemini", "deepseek", "grok", "universal"]


class TestCheatCodeRegistry:

    def test_all_codes_is_non_empty(self):
        assert len(ALL_CODES) > 10

    def test_all_codes_have_required_fields(self):
        for code in ALL_CODES:
            assert code.key,   f"Missing key on {code}"
            assert code.model, f"Missing model on {code.key}"
            assert code.title, f"Missing title on {code.key}"
            assert code.description, f"Missing description on {code.key}"

    def test_registry_keys_unique(self):
        keys = [c.key for c in ALL_CODES]
        assert len(keys) == len(set(keys)), "Duplicate cheat code keys"

    @pytest.mark.parametrize("model", KNOWN_MODELS)
    def test_get_codes_for_known_model(self, model: str):
        codes = get_codes_for_model(model)
        assert isinstance(codes, list)
        assert len(codes) > 0

    def test_get_codes_includes_universal_for_all_models(self):
        """Every model should include universal codes."""
        universal_keys = {c.key for c in BY_MODEL.get("universal", [])}
        for model in ["claude", "chatgpt", "gemini"]:
            codes = get_codes_for_model(model)
            code_keys = {c.key for c in codes}
            overlap = universal_keys & code_keys
            assert overlap, f"{model} missing universal codes"

    def test_get_selected_codes_returns_correct_objects(self):
        selected = get_selected_codes(["claude_xml", "token_budget"])
        keys = {c.key for c in selected}
        assert "claude_xml" in keys
        assert "token_budget" in keys

    def test_get_selected_codes_ignores_unknown_keys(self):
        # Should not raise, just skip unknown keys
        selected = get_selected_codes(["claude_xml", "NONEXISTENT_KEY"])
        assert len(selected) == 1
        assert selected[0].key == "claude_xml"

    def test_format_codes_for_prompt_returns_string(self):
        result = format_codes_for_prompt("claude")
        assert isinstance(result, str)
        assert len(result) > 100
        assert "XML" in result or "xml" in result.lower()

    def test_claude_has_no_prefill_code(self):
        """Claude 4.6 prefill deprecation must be in the registry."""
        assert "claude_no_prefill" in CHEATCODE_REGISTRY
        code = CHEATCODE_REGISTRY["claude_no_prefill"]
        assert "deprecated" in code.description.lower() or "DEPRECATED" in code.description

    def test_deepseek_r1_no_cot_code_exists(self):
        assert "deepseek_r1_reasoning" in CHEATCODE_REGISTRY
