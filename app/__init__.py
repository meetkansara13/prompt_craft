"""
app/__init__.py
================
Flask Application Factory — PromptCraft Pro v4.
Auto-loads GROQ_API_KEY from .env into session.
"""

from datetime import timedelta
from flask import Flask, render_template, jsonify, session
from config.settings import get_config, Config
from app.utils.errors import PromptCraftError
from app.utils.logger import get_logger

logger = get_logger(__name__)


def create_app(config: Config | None = None) -> Flask:
    cfg = config or get_config()

    app = Flask(
        __name__,
        template_folder="../templates",
        static_folder="../static",
    )

    app.secret_key = cfg.SECRET_KEY
    app.config["DEBUG"] = cfg.DEBUG
    app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(hours=cfg.SESSION_LIFETIME_HOURS)
    app.config["SESSION_COOKIE_HTTPONLY"] = True
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

    logger.info("Flask app created | env=%s debug=%s", cfg.ENV, cfg.DEBUG)

    from app.api import key_bp, generator_bp, optimizer_bp, history_bp, image_bp
    app.register_blueprint(key_bp)
    app.register_blueprint(generator_bp)
    app.register_blueprint(optimizer_bp)
    app.register_blueprint(history_bp)
    app.register_blueprint(image_bp)

    # Template list endpoint — UI uses this to populate template selector
    @app.get("/api/templates")
    def list_templates():
        from app.core.templates.registry import all_templates
        return jsonify({
            "templates": [
                {
                    "key":        t.key,
                    "icon":       t.icon,
                    "label":      t.label,
                    "category":   t.category,
                    "goal":       t.goal,
                    "framework":  t.framework,
                    "techniques": list(t.techniques),
                    "model":      t.model,
                    "complexity": t.complexity,
                }
                for t in all_templates()
            ]
        })

    # Auto-load Groq key from .env into session
    @app.before_request
    def auto_load_key():
        if not session.get("api_key") and cfg.GROQ_API_KEY:
            session.permanent = True
            session["api_key"] = cfg.GROQ_API_KEY

    @app.errorhandler(PromptCraftError)
    def handle_app_error(exc: PromptCraftError):
        return jsonify({"error": exc.message}), exc.http_status

    @app.get("/favicon.ico")
    def favicon():
        """Return a minimal 1x1 pixel ICO so browsers stop logging 404s."""
        from flask import Response
        # Minimal valid ICO file — 1×1 transparent pixel
        ico = (b'\x00\x00\x01\x00\x01\x00\x01\x01\x00\x00\x01\x00'
               b'\x18\x00(\x00\x00\x00\x16\x00\x00\x00(\x00\x00\x00'
               b'\x01\x00\x00\x00\x02\x00\x00\x00\x01\x00\x18\x00'
               b'\x00\x00\x00\x00\x04\x00\x00\x00\x00\x00\x00\x00'
               b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
               b'\xff\xff\xff\x00\x00\x00\x00\x00')
        return Response(ico, mimetype="image/x-icon",
                        headers={"Cache-Control": "public, max-age=86400"})

    @app.errorhandler(404)
    def not_found(_):
        return jsonify({"error": "Not found"}), 404

    @app.errorhandler(405)
    def method_not_allowed(_):
        return jsonify({"error": "Method not allowed"}), 405

    @app.errorhandler(500)
    def internal_error(exc):
        logger.exception("Unhandled 500 error")
        return jsonify({"error": "Internal server error"}), 500

    @app.get("/")
    def index():
        from app.services.history_service import HistoryService
        has_key    = bool(session.get("api_key"))
        hist_count = HistoryService(session).count()
        return render_template("index.html", has_key=has_key, hist_count=hist_count)

    return app