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
    log.info("  ᴡᴀιғᴜsᴄʀᴘєʀ — sᴛᴀʀᴛιηɢ ᴜᴘ...")
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
        log.info(f"sᴜᴅᴏ ᴜsєʀs ʟᴏᴀᴅєᴅ: {len(config.SUDO_USERS)}")
    except Exception as e:
        log.warning(f"could not load sudo users: {e}")
        config.SUDO_USERS = []

    for module in ALL_MODULES:
        try:
            importlib.import_module(module, package="WAIFUSCRPER.tools")
            log.info(f"  ✓ loaded: {module}")
        except Exception as e:
            log.error(f"  ✗ failed to load {module}: {e}")

    await app.start()
    me = await app.get_me()
    log.info(f"ʙᴏᴛ sᴛᴀʀᴛєᴅ ✅  @{me.username}  (id: {me.id})")

    total_handlers = sum(len(v) for v in app.dispatcher.groups.values())
    log.info(f"ʜᴀηᴅʟєʀs ʟᴏᴀᴅєᴅ: {total_handlers}")

    log.info("━" * 45)
    log.info("  ᴡᴀιғᴜsᴄʀᴘєʀ ιs ʀᴜηηιηɢ 🚀")
    log.info("━" * 45)

    await idle()

    try:
        await app.stop()
    except Exception:
        pass

    log.info("ᴡᴀιғᴜsᴄʀᴘєʀ sᴛᴏᴘᴘєᴅ. ɢᴏᴏᴅʙʏє 👋")


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
        
