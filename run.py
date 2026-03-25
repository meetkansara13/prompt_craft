"""
run.py
=======
Application entry point.

Usage:
    python run.py              # uses FLASK_ENV from .env
    FLASK_ENV=development python run.py
"""

from app import create_app
from config.settings import get_config

cfg = get_config()
app = create_app(cfg)

if __name__ == "__main__":
    print("\n  ✦  PromptCraft Pro v3")
    print("  ─────────────────────────────────────────")
    print("  http://localhost:5000")
    print(f"  ENV={cfg.ENV}  DEBUG={cfg.DEBUG}")
    print("  Press Ctrl+C to stop\n")
    app.run(host="0.0.0.0", port=5000, debug=cfg.DEBUG)
