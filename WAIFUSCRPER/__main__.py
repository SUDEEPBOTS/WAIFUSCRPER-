"""
WAIFUSCRPER — __main__.py
Entry point. Loads all plugins and starts the bot.
Logging is wired through WAIFUSCRPER.Logging (loguru-based).
"""

import asyncio
import importlib
import os

from pyrogram import idle

import config
from WAIFUSCRPER import app
from WAIFUSCRPER.Logging import LOGGER          # ← centralized logger
from WAIFUSCRPER.tools import ALL_MODULES
from WAIFUSCRPER.Database import get_sudo_users

# ── Module-level logger ────────────────────────────────────────────────────────
log = LOGGER(__name__)

# ── Ensure logs/ directory exists before loguru tries to write there ───────────
os.makedirs("logs", exist_ok=True)


# ══════════════════════════════════════════════════════════════════════════════
#  STARTUP
# ══════════════════════════════════════════════════════════════════════════════

async def init():

    log.info("━" * 45)
    log.info("  ᴡᴀɪꜰᴜsᴄʀᴘᴇʀ — sᴛᴀʀᴛɪɴɢ ᴜᴘ...")
    log.info("━" * 45)

    # ── Validate required config ───────────────────────────────────────────────
    missing = []
    if not config.BOT_TOKEN:
        missing.append("BOT_TOKEN")
    if not config.API_ID:
        missing.append("API_ID")
    if not config.API_HASH:
        missing.append("API_HASH")
    if not config.MONGO_URI:
        missing.append("MONGO_URI")

    if missing:
        for key in missing:
            log.error(f"❌ {key} ɴᴏᴛ sᴇᴛ ɪɴ .ᴇɴᴠ")
        log.error("ꜰɪʟʟ ᴀʟʟ ʀᴇQᴜɪʀᴇᴅ ᴠᴀʀs ᴀɴᴅ ʀᴇsᴛᴀʀᴛ — ᴀʙᴏʀᴛɪɴɢ.")
        exit(1)

    # ── Start Pyrogram bot client ──────────────────────────────────────────────
    await app.start()
    me = await app.get_me()
    log.info(f"ʙᴏᴛ sᴛᴀʀᴛᴇᴅ ✅  @{me.username}  (ID: {me.id})")

    # ── Load sudo users from DB into memory ────────────────────────────────────
    try:
        sudo_users = await get_sudo_users()
        config.SUDO_USERS = sudo_users
        log.info(f"sᴜᴅᴏ ᴜsᴇʀs ʟᴏᴀᴅᴇᴅ: {len(sudo_users)}")
    except Exception as e:
        log.warning(f"Could not load sudo users from DB: {e}")
        config.SUDO_USERS = []

    # ── Auto-load all plugins ──────────────────────────────────────────────────
    log.info("ʟᴏᴀᴅɪɴɢ ᴘʟᴜɢɪɴs...")

    loaded = 0
    failed = 0
    failed_list = []

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

    # ── Ready ──────────────────────────────────────────────────────────────────
    log.info("━" * 45)
    log.info("  ᴡᴀɪꜰᴜsᴄʀᴘᴇʀ ɪs ʀᴜɴɴɪɴɢ 🚀  |  sᴜᴅᴏ: /help")
    log.info("━" * 45)

    await idle()

    # ── Graceful shutdown ──────────────────────────────────────────────────────
    await app.stop()
    log.info("ᴡᴀɪꜰᴜsᴄʀᴘᴇʀ sᴛᴏᴘᴘᴇᴅ. ɢᴏᴏᴅʙʏᴇ 👋")


# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    asyncio.run(init())
    
