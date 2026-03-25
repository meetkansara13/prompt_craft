"""
app/utils/logger.py
====================
Centralized logging. Every module calls get_logger(__name__).
All logs go to console (and optionally a file in production).
"""

import logging
import sys
from config.settings import get_config

_cfg = get_config()


def get_logger(name: str) -> logging.Logger:
    """Return a configured logger for the given module name."""
    logger = logging.getLogger(name)

    # Avoid adding duplicate handlers if called multiple times
    if logger.handlers:
        return logger

    logger.setLevel(getattr(logging, _cfg.LOG_LEVEL.upper(), logging.INFO))

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(_cfg.LOG_FORMAT))
    logger.addHandler(handler)

    return logger
