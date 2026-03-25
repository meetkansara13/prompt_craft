"""
app/api/routes/optimizer_routes.py
=====================================
Blueprint for token optimization.
Route: /api/optimizer/optimize
"""

from flask import Blueprint, request, jsonify, session
from pydantic import ValidationError

from app.models.optimizer_models import OptimizeRequest
from app.services.optimizer_service import OptimizerService
from app.utils.errors import APIKeyMissingError, PromptCraftError
from app.utils.logger import get_logger

logger = get_logger(__name__)
bp = Blueprint("optimizer", __name__, url_prefix="/api/optimizer")


@bp.post("/optimize")
def optimize():
    """
    Optimize a prompt for token efficiency.

    Body (JSON): See OptimizeRequest model
    Returns:     OptimizeResponse as JSON
    """
    data = request.get_json(silent=True) or {}

    try:
        req = OptimizeRequest(**data)
    except ValidationError as exc:
        errors = exc.errors()
        first  = errors[0] if errors else {}
        msg    = f"{first.get('loc', ['?'])[0]}: {first.get('msg', 'Invalid')}"
        return jsonify({"error": msg}), 400

    key = session.get("api_key", "")
    if not key:
        return jsonify({"error": "No API key set."}), 401

    try:
        svc    = OptimizerService(api_key=key)
        result = svc.optimize(req)
        return jsonify({"ok": True, "data": result})

    except APIKeyMissingError as exc:
        return jsonify({"error": exc.message}), exc.http_status

    except PromptCraftError as exc:
        logger.error("PromptCraftError in optimize: %s", exc.message)
        return jsonify({"error": exc.message}), exc.http_status

    except Exception as exc:
        logger.exception("Unexpected error in optimize")
        return jsonify({"error": f"Unexpected error: {exc}"}), 500
