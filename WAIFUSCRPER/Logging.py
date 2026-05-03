"""
WAIFUSCRPER — logging.py
Centralized logger setup using loguru.
Import LOGGER from here everywhere in the project.

Usage:
    from WAIFUSCRPER.logging import LOGGER
    log = LOGGER(__name__)
    log.info("something")
"""

import sys
from loguru import logger

# ── Remove default loguru handler ──────────────────────────────────────────────
logger.remove()

# ── Console handler — colored, readable ───────────────────────────────────────
logger.add(
    sys.stdout,
    colorize=True,
    format=(
        "<green>{time:DD-MM-YYYY HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{line}</cyan> — "
        "<level>{message}</level>"
    ),
    level="INFO",
)

# ── File handler — full debug log, rotates daily ──────────────────────────────
logger.add(
    "logs/waifuscrper_{time:YYYY-MM-DD}.log",
    rotation="00:00",        # New file every midnight
    retention="7 days",      # Keep last 7 days
    compression="zip",       # Compress old logs
    format=(
        "{time:DD-MM-YYYY HH:mm:ss} | "
        "{level: <8} | "
        "{name}:{line} — {message}"
    ),
    level="DEBUG",
    encoding="utf-8",
)


def LOGGER(name: str):
    """
    Returns a loguru logger bound to the given module name.

    Usage:
        log = LOGGER(__name__)
        log.info("ʜᴇʟʟᴏ!")
    """
    return logger.bind(name=name)
  
