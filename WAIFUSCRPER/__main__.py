"""
WAIFUSCRPER — main.py
Entry point. Loads all plugins automatically and starts the bot.
"""

import asyncio
import importlib

from pyrogram import idle
from loguru import logger

import config
from WAIFUSCRPER import app
from WAIFUSCRPER.tools import ALL_MODULES
from WAIFUSCRPER.Database import get_sudo_users


async def init():
    logger.info("sᴛᴀʀᴛɪɴɢ ᴡᴀɪꜰᴜsᴄʀᴘᴇʀ...")

    # ── Validate required config ───────────────────────────────────────────────
    if not config.BOT_TOKEN:
        logger.error("ʙᴏᴛ_ᴛᴏᴋᴇɴ ɴᴏᴛ sᴇᴛ ɪɴ .ᴇɴᴠ — ᴀʙᴏʀᴛɪɴɢ.")
        exit(1)

    if not config.MONGO_URI:
        logger.error("ᴍᴏɴɢᴏ_ᴜʀɪ ɴᴏᴛ sᴇᴛ ɪɴ .ᴇɴᴠ — ᴀʙᴏʀᴛɪɴɢ.")
        exit(1)

    # ── Start bot ──────────────────────────────────────────────────────────────
    await app.start()
    logger.info("ʙᴏᴛ sᴛᴀʀᴛᴇᴅ ✅")

    # ── Load sudo users into memory ────────────────────────────────────────────
    try:
        sudo_users = await get_sudo_users()
        config.SUDO_USERS = sudo_users
        logger.info(f"sᴜᴅᴏ ᴜsᴇʀs ʟᴏᴀᴅᴇᴅ: {len(sudo_users)}")
    except Exception as e:
        logger.warning(f"Could not load sudo users: {e}")

    # ── Auto load all plugins ──────────────────────────────────────────────────
    loaded = 0
    failed = 0

    for module in ALL_MODULES:
        try:
            importlib.import_module(module, package="WAIFUSCRPER.tools")
            loaded += 1
        except Exception as e:
            logger.error(f"ꜰᴀɪʟᴇᴅ ᴛᴏ ʟᴏᴀᴅ {module}: {e}")
            failed += 1

    logger.info(
        f"ᴘʟᴜɢɪɴs ʟᴏᴀᴅᴇᴅ ✅  "
        f"[{loaded} sᴜᴄᴄᴇss / {failed} ꜰᴀɪʟᴇᴅ]"
    )

    # ── Keep running ───────────────────────────────────────────────────────────
    logger.info("ᴡᴀɪꜰᴜsᴄʀᴘᴇʀ ɪs ʀᴜɴɴɪɴɢ 🚀")
    await idle()

    # ── Graceful shutdown ──────────────────────────────────────────────────────
    await app.stop()
    logger.info("ᴡᴀɪꜰᴜsᴄʀᴘᴇʀ sᴛᴏᴘᴘᴇᴅ.")


if __name__ == "__main__":
    asyncio.run(init())
  
