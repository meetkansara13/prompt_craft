"""
tests/unit/test_prompt_engine.py
===================================
Unit tests for PromptEngine — no API calls, no Flask.
"""

import pytest
from app.core.engines.prompt_engine import PromptEngine


@pytest.fixture
def engine():
    return PromptEngine()


class TestPromptEngine:

    def test_build_system_prompt_returns_string(self, engine):
        result = engine.build_system_prompt(
            framework_key="RISEN",
            target_model="claude",
            selected_cheat_keys=[],
            selected_techniques=[],
        )
        assert isinstance(result, str)
        assert len(result) > 500

    def test_system_prompt_contains_framework_name(self, engine):
        result = engine.build_system_prompt(
            framework_key="RISEN",
            target_model="claude",
            selected_cheat_keys=[],
            selected_techniques=[],
        )
        assert "RISEN" in result

    def test_system_prompt_contains_json_schema(self, engine):
        result = engine.build_system_prompt(
            framework_key="COAST",
            target_model="gemini",
            selected_cheat_keys=[],
            selected_techniques=[],
        )
        assert "final_prompt" in result
        assert "quality_score" in result
        assert "model_variants" in result

    def test_system_prompt_contains_model_cheat_codes(self, engine):
        result = engine.build_system_prompt(
            framework_key="RTF",
            target_model="claude",
            selected_cheat_keys=["claude_xml"],
            selected_techniques=[],
        )
        assert "XML" in result or "xml" in result.lower()

    def test_system_prompt_contains_selected_techniques(self, engine):
        result = engine.build_system_prompt(
            framework_key="RISEN",
            target_model="claude",
            selected_cheat_keys=[],
            selected_techniques=["cot", "fewshot"],
        )
        assert "Chain-of-Thought" in result
        assert "Few-Shot" in result

    def test_build_user_message_contains_goal(self, engine):
        msg = engine.build_user_message(
            goal="Write product descriptions for my store",
            model="claude",
            category="writing",
            output_format="markdown",
            complexity="moderate",
            tones=["professional"],
            framework_key="RISEN",
            techniques=["cot"],
            cheat_codes=[],
        )
        assert "Write product descriptions for my store" in msg

    def test_build_user_message_contains_model(self, engine):
        msg = engine.build_user_message(
            goal="Test goal",
            model="deepseek",
            category="auto",
            output_format="auto",
            complexity="auto",
            tones=["direct"],
            framework_key="RTF",
            techniques=[],
            cheat_codes=[],
        )
        assert "deepseek" in msg

    def test_refine_system_prompt_contains_rules(self, engine):
        result = engine.build_refine_system_prompt()
        assert "REFINEMENT" in result.upper()
        assert "JSON" in result
        assert "improved_prompt" in result

    @pytest.mark.parametrize("framework", ["RISEN","COAST","BROKE","ROSES","CARE","RACE","TRACE","PTCF","RTF","APE"])
    def test_all_frameworks_produce_valid_system_prompt(self, engine, framework):
        result = engine.build_system_prompt(
            framework_key=framework,
            target_model="universal",
            selected_cheat_keys=[],
            selected_techniques=[],
        )
        assert isinstance(result, str)
        assert len(result) > 200
