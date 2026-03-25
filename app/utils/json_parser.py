"""
app/utils/json_parser.py
=========================
Safely extract and parse JSON from raw LLM text output.
LLMs sometimes wrap JSON in markdown fences or add preamble.
This module handles all those edge cases.
"""

import json
import re
from typing import Any

from app.utils.errors import JSONParseError
from app.utils.logger import get_logger

logger = get_logger(__name__)


def extract_json(raw_text: str) -> dict[str, Any]:
    """
    Extract a JSON object from raw LLM output.

    Strategy (in order):
    1. Strip markdown fences (```json ... ```)
    2. Find first { and last } to isolate the JSON object
    3. Parse with json.loads
    4. Raise JSONParseError with a helpful message on failure
    """
    if not raw_text or not raw_text.strip():
        raise JSONParseError("Empty response from AI.")

    # Step 1: Strip markdown code fences
    text = re.sub(r"```(?:json)?\s*", "", raw_text)
    text = text.replace("```", "").strip()

    # Step 2: Find first { and last }
    start = text.find("{")
    end   = text.rfind("}")

    if start == -1 or end == -1 or end <= start:
        logger.warning("No JSON object found in AI response. Raw (first 200 chars): %s", raw_text[:200])
        raise JSONParseError("AI response did not contain valid JSON.")

    json_str = text[start : end + 1]

    # Step 3: Parse
    try:
        return json.loads(json_str)
    except json.JSONDecodeError as exc:
        logger.warning("JSON parse failed: %s | Snippet: %s", exc, json_str[:300])
        raise JSONParseError(f"Could not parse AI response as JSON: {exc}") from exc
