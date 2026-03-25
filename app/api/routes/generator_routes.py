"""
app/api/routes/generator_routes.py
=====================================
Blueprint for prompt generation and refinement.
Routes: /api/generator/generate  /api/generator/refine

Routes are thin:
  1. Validate request with Pydantic
  2. Get API key from session
  3. Call GeneratorService
  4. Return JSON
"""

from flask import Blueprint, request, jsonify, session
from pydantic import ValidationError

from app.models.prompt_models import GenerateRequest, RefineRequest
from app.services.generator_service import GeneratorService
from app.utils.errors import (
    APIKeyMissingError, PromptCraftError, InvalidInputError,
)
from app.utils.logger import get_logger

logger = get_logger(__name__)
bp = Blueprint("generator", __name__, url_prefix="/api/generator")


def _get_api_key() -> str:
    key = session.get("api_key", "")
    if not key:
        raise APIKeyMissingError()
    return key


@bp.post("/generate")
def generate():
    """
    Generate a complete prompt from a user goal.

    Body (JSON): See GenerateRequest model
    Returns:     GenerateResponse as JSON
    """
    data = request.get_json(silent=True) or {}

    try:
        req = GenerateRequest(**data)
    except ValidationError as exc:
        errors = exc.errors()
        first  = errors[0] if errors else {}
        msg    = f"{first.get('loc', ['?'])[0]}: {first.get('msg', 'Invalid input')}"
        logger.warning("GenerateRequest validation failed: %s", errors)
        return jsonify({"error": msg}), 400

    try:
        api_key = _get_api_key()
        svc     = GeneratorService(api_key=api_key)
        result  = svc.generate(req)
        return jsonify({"ok": True, "data": result})

    except APIKeyMissingError as exc:
        return jsonify({"error": exc.message}), exc.http_status

    except PromptCraftError as exc:
        logger.error("PromptCraftError in generate: %s", exc.message)
        return jsonify({"error": exc.message}), exc.http_status

    except Exception as exc:
        logger.exception("Unexpected error in generate")
        return jsonify({"error": f"Unexpected error: {exc}"}), 500


@bp.post("/refine")
def refine():
    """
    Refine an existing prompt based on user feedback.

    Body (JSON): See RefineRequest model
    Returns:     RefineResponse as JSON
    """
    data = request.get_json(silent=True) or {}

    try:
        req = RefineRequest(**data)
    except ValidationError as exc:
        errors = exc.errors()
        first  = errors[0] if errors else {}
        msg    = f"{first.get('loc', ['?'])[0]}: {first.get('msg', 'Invalid input')}"
        return jsonify({"error": msg}), 400

    try:
        api_key = _get_api_key()
        svc     = GeneratorService(api_key=api_key)
        result  = svc.refine(req)
        return jsonify({"ok": True, "data": result})

    except APIKeyMissingError as exc:
        return jsonify({"error": exc.message}), exc.http_status

    except PromptCraftError as exc:
        logger.error("PromptCraftError in refine: %s", exc.message)
        return jsonify({"error": exc.message}), exc.http_status

    except Exception as exc:
        logger.exception("Unexpected error in refine")
        return jsonify({"error": f"Unexpected error: {exc}"}), 500
