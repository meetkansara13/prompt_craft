"""
tests/unit/test_json_parser.py
================================
Unit tests for the JSON extraction utility.
"""

import pytest
from app.utils.json_parser import extract_json
from app.utils.errors import JSONParseError


class TestExtractJson:

    def test_clean_json_string(self):
        raw = '{"score": 85, "grade": "Excellent"}'
        result = extract_json(raw)
        assert result["score"] == 85
        assert result["grade"] == "Excellent"

    def test_json_with_markdown_fence(self):
        raw = '```json\n{"key": "value"}\n```'
        result = extract_json(raw)
        assert result["key"] == "value"

    def test_json_with_preamble(self):
        raw = "Here is the JSON response:\n\n{\"answer\": 42}"
        result = extract_json(raw)
        assert result["answer"] == 42

    def test_json_with_trailing_text(self):
        raw = '{"ok": true} — end of response'
        result = extract_json(raw)
        assert result["ok"] is True

    def test_nested_json(self):
        raw = '{"analysis": {"score": 90, "items": ["a", "b"]}}'
        result = extract_json(raw)
        assert result["analysis"]["score"] == 90
        assert result["analysis"]["items"] == ["a", "b"]

    def test_empty_string_raises(self):
        with pytest.raises(JSONParseError, match="Empty response"):
            extract_json("")

    def test_no_json_object_raises(self):
        with pytest.raises(JSONParseError, match="valid JSON"):
            extract_json("This is just plain text with no JSON.")

    def test_invalid_json_raises(self):
        with pytest.raises(JSONParseError):
            extract_json("{broken json: true,}")

    def test_only_array_raises(self):
        # We only extract objects {}, not arrays []
        with pytest.raises(JSONParseError):
            extract_json("[1, 2, 3]")
