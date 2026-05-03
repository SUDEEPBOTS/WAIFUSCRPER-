"""
WAIFUSCRPER — __main__.py
Entry point. Loads all plugins and starts the bot.
"""

import asyncio
import importlib
import os

from pyrogram import idle

import config
from WAIFUSCRPER import app
from WAIFUSCRPER.Logging import LOGGER
from WAIFUSCRPER.tools import ALL_MODULES
from WAIFUSCRPER.Database import get_sudo_users

log = LOGGER(__name__)
os.makedirs("logs", exist_ok=True)


async def init():

    log.info("━" * 45)
    log.info("  ᴡᴀɪꜰᴜsᴄʀᴘᴇʀ — sᴛᴀʀᴛɪɴɢ ᴜᴘ...")
    log.info("━" * 45)

    # ── Validate required config ───────────────────────────────────────────────
    missing = []
    if not config.BOT_TOKEN:  missing.append("BOT_TOKEN")
    if not config.API_ID:     missing.append("API_ID")
    if not config.API_HASH:   missing.append("API_HASH")
    if not config.MONGO_URI:  missing.append("MONGO_URI")

    if missing:
        for key in missing:
            log.error(f"❌ {key} not set in .env")
        exit(1)

    # ── Start bot FIRST ────────────────────────────────────────────────────────
    await app.start()
    me = await app.get_me()
    log.info(f"ʙᴏᴛ sᴛᴀʀᴛᴇᴅ ✅  @{me.username}  (ID: {me.id})")

    # ── Load sudo users ────────────────────────────────────────────────────────
    try:
        config.SUDO_USERS = await get_sudo_users()
        log.info(f"sᴜᴅᴏ ᴜsᴇʀs ʟᴏᴀᴅᴇᴅ: {len(config.SUDO_USERS)}")
    except Exception as e:
        log.warning(f"Could not load sudo users: {e}")
        config.SUDO_USERS = []

    # ── Load plugins AFTER app.start() ────────────────────────────────────────
    log.info("ʟᴏᴀᴅɪɴɢ ᴘʟᴜɢɪɴs...")
    loaded, failed, failed_list = 0, 0, []

    for module in ALL_MODULES:
        try:
            importlib.import_module(module, package="WAIFUSCRPER.tools")
            log.info(f"  ✅  {module}")
            loaded += 1
        except Exception as e:
            log.error(f"  ❌  {module}  →  {e}")
            failed_list.append(module)
            failed += 1

    log.info(
        f"ᴘʟᴜɢɪɴs: {loaded} ʟᴏᴀᴅᴇᴅ"
        + (f"  |  {failed} ꜰᴀɪʟᴇᴅ → {failed_list}" if failed else "")
    )

    log.info("━" * 45)
    log.info(f"  ʜᴀɴᴅʟᴇʀs ʀᴇɢɪsᴛᴇʀᴇᴅ: {sum(len(v) for v in app.dispatcher.groups.values())}")
    log.info("  ᴡᴀɪꜰᴜsᴄʀᴘᴇʀ ɪs ʀᴜɴɴɪɴɢ 🚀")
    log.info("━" * 45)

    await idle()
    await app.stop()
    log.info("ᴡᴀɪꜰᴜsᴄʀᴘᴇʀ sᴛᴏᴘᴘᴇᴅ. ɢᴏᴏᴅʙʏᴇ 👋")


if __name__ == "__main__":
    asyncio.run(init())
