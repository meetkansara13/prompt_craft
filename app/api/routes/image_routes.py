"""
app/api/routes/image_routes.py
================================
Blueprint for Image → Prompt feature.
Route: POST /api/image/analyze

Accepts base64 image + framework + prompt_type.
Returns full visual analysis + generated build-ready prompt.
"""

from flask import Blueprint, request, jsonify, session
from pydantic import ValidationError

from app.models.image_models import ImageAnalyzeRequest
from app.services.vision_service import VisionService
from app.utils.errors import APIKeyMissingError, PromptCraftError
from app.utils.logger import get_logger

logger = get_logger(__name__)
bp = Blueprint("image", __name__, url_prefix="/api/image")


@bp.post("/analyze")
def analyze():
    """
    Analyze an uploaded image and generate a build-ready prompt.

    Body (JSON):
      image_base64  : base64 encoded image string
      image_type    : MIME type e.g. image/jpeg, image/png (default: image/jpeg)
      framework     : react | nextjs | vue | html | tailwind | flutter
      prompt_type   : build | improve | describe

    Returns: ImagePromptResponse as JSON
    """
    data = request.get_json(silent=True) or {}

    # Validate request
    try:
        req = ImageAnalyzeRequest(**data)
    except ValidationError as exc:
        errors = exc.errors()
        first  = errors[0] if errors else {}
        msg    = f"{first.get('loc', ['?'])[0]}: {first.get('msg', 'Invalid input')}"
        logger.warning("ImageAnalyzeRequest validation failed: %s", errors)
        return jsonify({"error": msg}), 400

    # Get API key
    key = session.get("api_key", "")
    if not key:
        return jsonify({"error": "No API key set."}), 401

    try:
        svc    = VisionService(api_key=key)
        result = svc.analyze(req)
        return jsonify({"ok": True, "data": result})

    except APIKeyMissingError as exc:
        return jsonify({"error": exc.message}), exc.http_status

    except PromptCraftError as exc:
        logger.error("PromptCraftError in image analyze: %s", exc.message)
        return jsonify({"error": exc.message}), exc.http_status

    except Exception as exc:
        logger.exception("Unexpected error in image analyze")
        return jsonify({"error": f"Image analysis failed: {exc}"}), 500


@bp.get("/frameworks")
def list_frameworks():
    """Return available frameworks and prompt types for the UI."""
    return jsonify({
        "frameworks": [
            {"key": "react",    "label": "React",         "icon": "⚛️",  "desc": "React + hooks + CSS Modules"},
            {"key": "nextjs",   "label": "Next.js",       "icon": "▲",   "desc": "Next.js 14 + App Router + Tailwind"},
            {"key": "vue",      "label": "Vue 3",         "icon": "💚",  "desc": "Vue 3 + Composition API"},
            {"key": "html",     "label": "HTML/CSS",      "icon": "🌐",  "desc": "Semantic HTML5 + Vanilla CSS"},
            {"key": "tailwind", "label": "Tailwind",      "icon": "🎨",  "desc": "HTML + Tailwind CSS + Alpine.js"},
            {"key": "flutter",  "label": "Flutter",       "icon": "🐦",  "desc": "Flutter + Dart + Material 3"},
        ],
        "prompt_types": [
            {"key": "build",    "label": "Build This",    "icon": "🔨", "desc": "Generate a prompt to recreate this UI from scratch"},
            {"key": "improve",  "label": "Improve This",  "icon": "⚡", "desc": "Generate a prompt to analyze and improve this UI"},
            {"key": "describe", "label": "Describe This", "icon": "📝", "desc": "Generate a detailed description of this UI"},
        ],
    })
