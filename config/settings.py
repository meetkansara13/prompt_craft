"""
config/settings.py
==================
Central configuration. All settings come from environment variables
(loaded from .env in development). Never hardcode secrets here.
"""

import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    # ── Flask ──────────────────────────────────────────
    SECRET_KEY: str = os.getenv("FLASK_SECRET_KEY", "dev-secret-change-in-production")
    DEBUG: bool     = os.getenv("FLASK_DEBUG", "false").lower() == "true"
    ENV: str        = os.getenv("FLASK_ENV", "production")

    # ── Groq ───────────────────────────────────────────
    GROQ_API_KEY: str    = os.getenv("GROQ_API_KEY", "")
    GROQ_MODEL: str      = "llama-3.3-70b-versatile"
    GROQ_MAX_TOKENS: int = 8000
    GROQ_TIMEOUT: int    = 120

    # ── Session ────────────────────────────────────────
    SESSION_LIFETIME_HOURS: int = int(os.getenv("SESSION_LIFETIME_HOURS", "8"))
    MAX_HISTORY: int            = int(os.getenv("MAX_HISTORY", "30"))

    # ── Logging ────────────────────────────────────────
    LOG_LEVEL: str  = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT: str = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"


class DevelopmentConfig(Config):
    DEBUG = True
    ENV   = "development"


class ProductionConfig(Config):
    DEBUG = False
    ENV   = "production"


class TestingConfig(Config):
    TESTING          = True
    DEBUG            = True
    GROQ_API_KEY     = "gsk_test-fake-key-for-testing"
    WTF_CSRF_ENABLED = False


def get_config() -> Config:
    env = os.getenv("FLASK_ENV", "production").lower()
    mapping = {
        "development": DevelopmentConfig,
        "production":  ProductionConfig,
        "testing":     TestingConfig,
    }
    return mapping.get(env, ProductionConfig)()
