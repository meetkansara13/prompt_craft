"""
app/api/routes/key_routes.py
==============================
Blueprint for API key management.
Updated for Groq — keys start with gsk_
Routes: /api/key/set  /api/key/clear  /api/key/status
"""

from flask import Blueprint, request, jsonify, session
from app.services.anthropic_client import AnthropicClient
from app.utils.errors import APIKeyInvalidError, APIKeyMissingError, AnthropicAPIError
from app.utils.logger import get_logger

logger = get_logger(__name__)
bp = Blueprint("key", __name__, url_prefix="/api/key")


@bp.post("/set")
def set_key():
    """Validate and store a Groq API key in the session."""
    data = request.get_json(silent=True) or {}
    key  = data.get("key", "").strip()

    if not key:
        return jsonify({"ok": False, "error": "No key provided."}), 400

    try:
        AnthropicClient.verify_key(key)
        session.permanent  = True
        session["api_key"] = key
        masked = key[:10] + "••••" + key[-4:]
        logger.info("Groq API key set | masked=%s", masked)
        return jsonify({"ok": True, "masked": masked})

    except (APIKeyInvalidError, APIKeyMissingError) as exc:
        return jsonify({"ok": False, "error": exc.message}), exc.http_status

    except AnthropicAPIError as exc:
        return jsonify({"ok": False, "error": exc.message}), exc.http_status


@bp.post("/clear")
def clear_key():
    session.pop("api_key", None)
    logger.info("API key cleared")
    return jsonify({"ok": True})


@bp.get("/status")
def key_status():
    key = session.get("api_key", "")
    if key:
        masked = key[:10] + "••••" + key[-4:]
        return jsonify({"set": True, "masked": masked})
    return jsonify({"set": False})
