"""
WAIFUSCRPER — config.py
Loads all configuration from .env file.
"""

import os
from dotenv import load_dotenv

load_dotenv()

# ── Bot Config ────────────────────────────────────────────
BOT_TOKEN   = os.getenv("BOT_TOKEN", "")
API_ID      = int(os.getenv("API_ID", 0))
API_HASH    = os.getenv("API_HASH", "")
OWNER_ID    = int(os.getenv("OWNER_ID", 0))

# ── Sudo Users (from .env, space-separated IDs) ───────────
# Note: These get overwritten at runtime with DB values
_sudo_env   = os.getenv("SUDO_USERS", "")
SUDO_USERS: list[int] = (
    [int(x) for x in _sudo_env.split() if x.isdigit()]
    if _sudo_env.strip() else []
)

# ── MongoDB ───────────────────────────────────────────────
MONGO_URI         = os.getenv("MONGO_URI", "")
DB_NAME           = os.getenv("DB_NAME", "waifuscrper")
COLLECTION_NAME   = os.getenv("COLLECTION_NAME", "waifus")

# ── Logger ────────────────────────────────────────────────
LOGGER_ID         = int(os.getenv("LOGGER_ID", 0)) or None

# ── Target Channel ────────────────────────────────────────
TARGET_CHANNEL    = os.getenv("TARGET_CHANNEL", "") or None

# ── Userbot (String Session) ──────────────────────────────
STRING_SESSION    = os.getenv("STRING_SESSION", "") or None

# ── Waifu Settings ────────────────────────────────────────
APPROVE_MODE      = os.getenv("APPROVE_MODE", "false").lower() == "true"
AUTO_FETCH_NEW    = os.getenv("AUTO_FETCH_NEW", "false").lower() == "true"

# ── Image Upload ──────────────────────────────────────────
CATBOX_HASH       = os.getenv("CATBOX_HASH", "")
IMGBB_KEY         = os.getenv("IMGBB_KEY", "")

# ── Keyword / Caption Parsing ─────────────────────────────
RARITY_KEYWORD    = os.getenv("RARITY_KEYWORD", "Rarity")

