"""
tests/integration/test_routes.py
===================================
Integration tests for all Flask routes.
Uses Flask's test client — no real Anthropic calls.
We mock AnthropicClient.complete() to return controlled JSON.
"""

import json
from unittest.mock import patch, MagicMock
import pytest

from app import create_app
from config.settings import TestingConfig

# ── Reusable mock response payloads ──────────────────────────────────────────

MOCK_GENERATE_RESPONSE = json.dumps({
    "analysis": {
        "detected_intent": "Test intent",
        "task_type": "Content Generation",
        "detected_domain": "Testing",
        "complexity": "Simple",
        "key_requirements": ["req1", "req2"],
        "ambiguities_resolved": [],
    },
    "quality_score": {
        "score": 90, "grade": "Excellent",
        "clarity": 88, "specificity": 91,
        "technique_use": 89, "completeness": 92,
        "improvements": [],
    },
    "prompt_sections": {
        "system_context": "You are a test assistant.",
        "context_background": "Context here.",
        "main_task": "Do the task.",
        "examples_format": "Example here.",
        "constraints_rules": "Rule 1. Rule 2.",
        "self_check": "Verify your output.",
    },
    "final_prompt": "This is the final prompt. " * 20,
    "token_optimized_prompt": "Optimized prompt. " * 10,
    "model_variants": {
        "claude": "Claude variant",
        "chatgpt": "ChatGPT variant",
        "gemini": "Gemini variant",
        "gpt5": "GPT-5 variant",
        "deepseek": "DeepSeek variant",
        "grok": "Grok variant",
        "universal": "Universal variant",
    },
    "model_tips": {
        "claude":    [{"icon": "🏷️", "title": "Tip", "desc": "Description", "code": None}],
        "chatgpt":   [{"icon": "🎭", "title": "Tip", "desc": "Description", "code": None}],
        "gemini":    [{"icon": "📐", "title": "Tip", "desc": "Description", "code": None}],
        "gpt5":      [{"icon": "⚡", "title": "Tip", "desc": "Description", "code": None}],
        "deepseek":  [{"icon": "🧠", "title": "Tip", "desc": "Description", "code": None}],
        "grok":      [{"icon": "🔍", "title": "Tip", "desc": "Description", "code": None}],
        "universal": [{"icon": "✂️", "title": "Tip", "desc": "Description", "code": None}],
    },
    "explanations": [
        {"icon": "✦", "color": "teal", "title": "CoT", "desc": "Chain-of-thought explanation."},
    ],
})

MOCK_REFINE_RESPONSE = json.dumps({
    "improved_prompt": "Improved prompt text here. " * 10,
    "token_optimized_prompt": "Optimized improved. " * 5,
    "changes_made": ["Made constraints more specific", "Added few-shot example"],
    "quality_score": {
        "score": 95, "grade": "Elite",
        "clarity": 95, "specificity": 95,
        "technique_use": 94, "completeness": 96,
        "improvements": [],
    },
})

MOCK_OPTIMIZE_RESPONSE = json.dumps({
    "analysis": {
        "original_tokens": 200,
        "waste_pct": 40.0,
        "token_breakdown": [
            {"category": "Task Instructions", "tokens": 80, "pct": 40.0, "color": "teal"},
            {"category": "Filler Phrases", "tokens": 60, "pct": 30.0, "color": "rose"},
            {"category": "Role/Context", "tokens": 60, "pct": 30.0, "color": "gold"},
        ],
        "issues": [
            {"severity": "high", "icon": "⚠️", "title": "Redundant politeness",
             "desc": "Multiple filler phrases add no value.", "save": "~40 tokens"},
        ],
    },
    "versions": {
        "balanced":   {"prompt": "Balanced prompt.", "tokens": 120, "pct": 40.0, "techniques": ["Semantic Trim"]},
        "aggressive": {"prompt": "Aggressive.", "tokens": 80,  "pct": 60.0, "techniques": ["CoD"]},
        "ultra":      {"prompt": "Ultra.", "tokens": 50,  "pct": 75.0, "techniques": ["All"]},
    },
    "quality": {
        "semantic_retention": 98.0, "intent_clarity": 97.0,
        "readability": 92.0, "accuracy_risk": 4.0,
    },
    "savings": {
        "tokens_saved": 80, "cost_pct": 40.0, "speed_pct": 24.0,
        "example": "$4.00 → $2.40 at 100k requests/month",
    },
    "techniques_applied": [
        {"icon": "✂️", "name": "Semantic Trim", "desc": "Removed redundant phrases.", "saved": 40},
    ],
    "model_tips": {
        "claude":    [{"icon": "🔖", "title": "Caching", "desc": "Enable prompt caching.", "code": None}],
        "chatgpt":   [{"icon": "🎭", "title": "JSON Mode", "desc": "Use JSON mode.", "code": None}],
        "gemini":    [{"icon": "📐", "title": "Schema", "desc": "Use responseSchema.", "code": None}],
        "deepseek":  [{"icon": "🧠", "title": "R1", "desc": "No CoT needed.", "code": None}],
        "universal": [{"icon": "✂️", "title": "Filler", "desc": "Remove filler.", "code": None}],
    },
})


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def app():
    return create_app(TestingConfig())


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def authed_client(client):
    """Client with a fake API key in session."""
    with client.session_transaction() as sess:
        sess["api_key"] = "gsk_fake-test-key-abc123"
    return client


# ── Key Routes ────────────────────────────────────────────────────────────────

class TestKeyRoutes:

    def test_key_status_no_key(self, client):
        r = client.get("/api/key/status")
        assert r.status_code == 200
        data = r.get_json()
        assert data["set"] is False

    def test_key_status_with_key(self, authed_client):
        r = authed_client.get("/api/key/status")
        assert r.status_code == 200
        data = r.get_json()
        assert data["set"] is True
        assert "masked" in data

    def test_key_set_missing_key_returns_400(self, client):
        r = client.post("/api/key/set",
                        data=json.dumps({}),
                        content_type="application/json")
        assert r.status_code == 400

    def test_key_set_invalid_format_returns_401(self, client):
        with patch("app.services.anthropic_client.AnthropicClient.verify_key",
                   side_effect=Exception("bad key")):
            r = client.post("/api/key/set",
                            data=json.dumps({"key": "not-a-real-key"}),
                            content_type="application/json")
        assert r.status_code in (400, 401, 502)

    def test_key_clear(self, authed_client):
        r = authed_client.post("/api/key/clear")
        assert r.status_code == 200
        assert r.get_json()["ok"] is True
        # Key should be gone now
        status = authed_client.get("/api/key/status").get_json()
        assert status["set"] is False


# ── Generator Routes ──────────────────────────────────────────────────────────

class TestGeneratorRoutes:

    def test_generate_no_key_returns_401(self, client):
        r = client.post("/api/generator/generate",
                        data=json.dumps({"goal": "Write a product description for my store"}),
                        content_type="application/json")
        assert r.status_code == 401

    def test_generate_missing_goal_returns_400(self, authed_client):
        r = authed_client.post("/api/generator/generate",
                               data=json.dumps({}),
                               content_type="application/json")
        assert r.status_code == 400

    def test_generate_goal_too_short_returns_400(self, authed_client):
        r = authed_client.post("/api/generator/generate",
                               data=json.dumps({"goal": "Hi"}),
                               content_type="application/json")
        assert r.status_code == 400

    def test_generate_invalid_model_returns_400(self, authed_client):
        r = authed_client.post("/api/generator/generate",
                               data=json.dumps({
                                   "goal": "Write a product description for my store",
                                   "model": "invalid_model_xyz",
                               }),
                               content_type="application/json")
        assert r.status_code == 400

    def test_generate_success(self, authed_client):
        with patch("app.services.anthropic_client.AnthropicClient.complete",
                   return_value=MOCK_GENERATE_RESPONSE):
            r = authed_client.post("/api/generator/generate",
                                   data=json.dumps({
                                       "goal": "Write compelling product descriptions for my handmade jewellery store",
                                       "model": "claude",
                                       "framework": "RISEN",
                                   }),
                                   content_type="application/json")
        assert r.status_code == 200
        data = r.get_json()
        assert data["ok"] is True
        assert "data" in data
        assert "final_prompt" in data["data"]
        assert "quality_score" in data["data"]

    def test_generate_all_valid_frameworks(self, authed_client):
        frameworks = ["RISEN", "COAST", "BROKE", "ROSES", "CARE", "RACE", "TRACE", "PTCF", "RTF", "APE"]
        with patch("app.services.anthropic_client.AnthropicClient.complete",
                   return_value=MOCK_GENERATE_RESPONSE):
            for fw in frameworks:
                r = authed_client.post("/api/generator/generate",
                                       data=json.dumps({
                                           "goal": "Write product descriptions for my online store",
                                           "framework": fw,
                                       }),
                                       content_type="application/json")
                assert r.status_code == 200, f"Framework {fw} failed with {r.status_code}"

    def test_refine_success(self, authed_client):
        with patch("app.services.anthropic_client.AnthropicClient.complete",
                   return_value=MOCK_REFINE_RESPONSE):
            r = authed_client.post("/api/generator/refine",
                                   data=json.dumps({
                                       "current_prompt": "You are an expert writer. " * 20,
                                       "feedback": "Make the constraints more specific",
                                   }),
                                   content_type="application/json")
        assert r.status_code == 200
        data = r.get_json()
        assert data["ok"] is True
        assert "improved_prompt" in data["data"]
        assert "changes_made" in data["data"]

    def test_refine_missing_fields_returns_400(self, authed_client):
        r = authed_client.post("/api/generator/refine",
                               data=json.dumps({"current_prompt": "Some prompt"}),
                               content_type="application/json")
        assert r.status_code == 400


# ── Optimizer Routes ──────────────────────────────────────────────────────────

class TestOptimizerRoutes:

    def test_optimize_no_key_returns_401(self, client):
        r = client.post("/api/optimizer/optimize",
                        data=json.dumps({"prompt": "Please help me write a product description."}),
                        content_type="application/json")
        assert r.status_code == 401

    def test_optimize_missing_prompt_returns_400(self, authed_client):
        r = authed_client.post("/api/optimizer/optimize",
                               data=json.dumps({}),
                               content_type="application/json")
        assert r.status_code == 400

    def test_optimize_invalid_level_returns_400(self, authed_client):
        r = authed_client.post("/api/optimizer/optimize",
                               data=json.dumps({
                                   "prompt": "You are a helpful assistant. " * 5,
                                   "level": "extreme",
                               }),
                               content_type="application/json")
        assert r.status_code == 400

    def test_optimize_success(self, authed_client):
        with patch("app.services.anthropic_client.AnthropicClient.complete",
                   return_value=MOCK_OPTIMIZE_RESPONSE):
            r = authed_client.post("/api/optimizer/optimize",
                                   data=json.dumps({
                                       "prompt": "You are a helpful, friendly assistant. Please make sure to answer questions in detail and please be polite at all times.",
                                       "level": "balanced",
                                   }),
                                   content_type="application/json")
        assert r.status_code == 200
        data = r.get_json()
        assert data["ok"] is True
        assert "versions" in data["data"]
        assert "balanced" in data["data"]["versions"]

    def test_optimize_all_levels(self, authed_client):
        with patch("app.services.anthropic_client.AnthropicClient.complete",
                   return_value=MOCK_OPTIMIZE_RESPONSE):
            for level in ["balanced", "aggressive", "ultra"]:
                r = authed_client.post("/api/optimizer/optimize",
                                       data=json.dumps({
                                           "prompt": "You are a helpful assistant that always provides detailed answers.",
                                           "level": level,
                                       }),
                                       content_type="application/json")
                assert r.status_code == 200, f"Level {level} failed"


# ── History Routes ────────────────────────────────────────────────────────────

class TestHistoryRoutes:

    def test_list_empty_initially(self, client):
        r = client.get("/api/history/list")
        assert r.status_code == 200
        data = r.get_json()
        assert data["items"] == []

    def test_save_and_list(self, client):
        payload = {
            "goal": "Write product descriptions for my store",
            "model": "claude",
            "framework": "RISEN",
            "score": 88,
            "prompt": "Full prompt text here.",
            "full_data": {"quality_score": {"score": 88}},
        }
        save_r = client.post("/api/history/save",
                             data=json.dumps(payload),
                             content_type="application/json")
        assert save_r.status_code == 200
        assert save_r.get_json()["ok"] is True

        list_r = client.get("/api/history/list")
        items  = list_r.get_json()["items"]
        assert len(items) == 1
        assert items[0]["goal"] == "Write product descriptions for my store"
        assert items[0]["score"] == 88

    def test_save_and_get(self, client):
        payload = {
            "goal": "Test goal for retrieval",
            "model": "gemini",
            "framework": "PTCF",
            "score": 75,
            "prompt": "Test prompt.",
            "full_data": {"test": True},
        }
        save_r = client.post("/api/history/save",
                             data=json.dumps(payload),
                             content_type="application/json")
        entry_id = save_r.get_json()["id"]

        get_r = client.get(f"/api/history/{entry_id}")
        assert get_r.status_code == 200
        item = get_r.get_json()["item"]
        assert item["goal"] == "Test goal for retrieval"
        assert item["full_data"]["test"] is True

    def test_get_nonexistent_id_returns_404(self, client):
        r = client.get("/api/history/99999")
        assert r.status_code == 404

    def test_clear_history(self, client):
        # Save two entries
        for i in range(2):
            client.post("/api/history/save",
                        data=json.dumps({
                            "goal": f"Goal {i}", "model": "claude",
                            "framework": "RTF", "score": 80,
                            "prompt": "Prompt.", "full_data": {},
                        }),
                        content_type="application/json")

        assert len(client.get("/api/history/list").get_json()["items"]) == 2

        clear_r = client.post("/api/history/clear")
        assert clear_r.status_code == 200

        assert len(client.get("/api/history/list").get_json()["items"]) == 0

    def test_history_missing_required_fields_returns_400(self, client):
        r = client.post("/api/history/save",
                        data=json.dumps({"goal": "no score or model"}),
                        content_type="application/json")
        assert r.status_code == 400


# ── Page Route ────────────────────────────────────────────────────────────────

class TestPageRoutes:

    def test_index_returns_200(self, client):
        r = client.get("/")
        assert r.status_code == 200

    def test_404_returns_json(self, client):
        r = client.get("/nonexistent-route-xyz")
        assert r.status_code == 404
