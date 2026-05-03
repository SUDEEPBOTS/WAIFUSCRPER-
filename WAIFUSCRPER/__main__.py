import asyncio
import os
import importlib

from pyrogram import idle

import config
from WAIFUSCRPER import app
from WAIFUSCRPER.Logging import LOGGER
from WAIFUSCRPER.Database import get_sudo_users
from WAIFUSCRPER.tools import ALL_MODULES

log = LOGGER(__name__)
os.makedirs("logs", exist_ok=True)


async def init():
    log.info("━" * 45)
    log.info("  ᴡᴀɪꜰᴜsᴄʀᴘᴇʀ — sᴛᴀʀᴛɪɴɢ ᴜᴘ...")
    log.info("━" * 45)

    missing = []
    if not config.BOT_TOKEN:  missing.append("BOT_TOKEN")
    if not config.API_ID:     missing.append("API_ID")
    if not config.API_HASH:   missing.append("API_HASH")
    if not config.MONGO_URI:  missing.append("MONGO_URI")

    if missing:
        for key in missing:
            log.error(f"❌ {key} not set in .env")
        exit(1)

    try:
        config.SUDO_USERS = await get_sudo_users()
        log.info(f"sᴜᴅᴏ ᴜsᴇʀs ʟᴏᴀᴅᴇᴅ: {len(config.SUDO_USERS)}")
    except Exception as e:
        log.warning(f"Could not load sudo users: {e}")
        config.SUDO_USERS = []

    # YUKIWAFUS WALA FAIL-PROOF CUSTOM LOADER 🔥
    for module in ALL_MODULES:
        try:
            importlib.import_module(module, package="WAIFUSCRPER.tools")
            log.info(f"  ✓ Loaded: {module}")
        except Exception as e:
            log.error(f"  ✗ Failed to load {module}: {e}")

    await app.start()
    me = await app.get_me()
    log.info(f"ʙᴏᴛ sᴛᴀʀᴛᴇᴅ ✅  @{me.username}  (ID: {me.id})")
    
    total_handlers = sum(len(v) for v in app.dispatcher.groups.values())
    log.info(f"ʜᴀɴᴅʟᴇʀs: {total_handlers}")

    log.info("━" * 45)
    log.info("  ᴡᴀɪꜰᴜsᴄʀᴘᴇʀ ɪs ʀᴜɴɴɪɴɢ 🚀")
    log.info("━" * 45)

    await idle()
    
    try:
        await app.stop()
    except Exception:
        pass # Ignored Python 3.12 strict shutdown crash
        
    log.info("ᴡᴀɪꜰᴜsᴄʀᴘᴇʀ sᴛᴏᴘᴘᴇᴅ. ɢᴏᴏᴅʙʏᴇ 👋")


if __name__ == "__main__":
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    try:
        loop.run_until_complete(init())
    except KeyboardInterrupt:
        pass
        
