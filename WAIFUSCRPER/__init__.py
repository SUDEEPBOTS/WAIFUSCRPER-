"""
WAIFUSCRPER — __init__.py
Pyrogram Client initialization.
Plugins are imported HERE so decorators register before app.start()
"""

from pyrogram import Client
from loguru import logger

import config

# ── Bot Client ─────────────────────────────────────────────────────────────────
app = Client(
    name="WAIFUSCRPER",
    api_id=config.API_ID,
    api_hash=config.API_HASH,
    bot_token=config.BOT_TOKEN,
    sleep_threshold=60,
    max_concurrent_transmissions=5,
)

logger.info("ᴘʏʀᴏɢʀᴀᴍ ᴄʟɪᴇɴᴛ ɪɴɪᴛɪᴀʟɪᴢᴇᴅ ✅")

# ── Import all plugins HERE so @app.on_message decorators fire before start() ──
import importlib
from WAIFUSCRPER.tools import ALL_MODULES

for _mod in ALL_MODULES:
    try:
        importlib.import_module(_mod, package="WAIFUSCRPER.tools")
        logger.info(f"  ✅  {_mod}")
    except Exception as e:
        logger.error(f"  ❌  {_mod}  →  {e}")
        
