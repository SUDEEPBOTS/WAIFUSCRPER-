"""
WAIFUSCRPER — __init__.py
Pyrogram Client with plugins parameter — handles handler registration automatically.
"""

from pyrogram import Client
from loguru import logger

import config

app = Client(
    name="WAIFUSCRPER",
    api_id=config.API_ID,
    api_hash=config.API_HASH,
    bot_token=config.BOT_TOKEN,
    sleep_threshold=60,
    max_concurrent_transmissions=5,
)

logger.info("ᴘʏʀᴏɢʀᴀᴍ ᴄʟɪᴇɴᴛ ɪɴɪᴛɪᴀʟɪᴢᴇᴅ ✅")
