"""
WAIFUSCRPER — tools/start.py
Handles:
  • /start command  → Main menu
  • menu_home callback → Back to main menu
"""

from pyrogram import Client, filters
from pyrogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)

import config
from WAIFUSCRPER import app
from WAIFUSCRPER.Logging import LOGGER
from WAIFUSCRPER.Database import get_waifu_count

log = LOGGER(__name__)

# ══════════════════════════════════════════════════════════════════════════════
#  START MESSAGE
# ══════════════════════════════════════════════════════════════════════════════

START_TEXT = (
    "🌸 <b>ᴡᴀɪꜰᴜsᴄʀᴘᴇʀ</b> — ʏᴏᴜʀ ᴡᴀɪꜰᴜ ᴄᴏʟʟᴇᴄᴛɪᴏɴ ʙᴏᴛ!\n\n"
    "━━━━━━━━━━━━━━━━━━━━━\n"
    "🤖 ᴍᴀɪɴ ꜰᴇᴀᴛᴜʀᴇs:\n"
    "  • ᴛᴇʟᴇɢʀᴀᴍ ᴄʜᴀɴɴᴇʟ sᴇ ᴡᴀɪꜰᴜs sᴄʀᴀᴘᴇ ᴋᴀʀᴏ\n"
    "  • ᴀᴘᴘʀᴏᴠᴇ / ᴀᴜᴛᴏ ᴍᴏᴅᴇ\n"
    "  • ᴍᴏɴɢᴏᴅʙ ᴍᴇɪɴ sᴀᴠᴇ\n"
    "  • ᴄᴀᴛʙᴏx + ɪᴍɢʙʙ ɪᴍᴀɢᴇ ʜᴏsᴛɪɴɢ\n"
    "━━━━━━━━━━━━━━━━━━━━━\n\n"
    "Niche se option chunlo 👇"
)


def _main_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("⚙️ Config",     callback_data="menu_config_p1"),
            InlineKeyboardButton("❓ Help",        callback_data="menu_help"),
        ],
        [
            InlineKeyboardButton("📊 Group Stats", callback_data="menu_stats"),
        ],
    ])


# ══════════════════════════════════════════════════════════════════════════════
#  /start COMMAND
# ══════════════════════════════════════════════════════════════════════════════

@app.on_message(filters.command("start") & (filters.private | filters.group))
async def cmd_start(client: Client, message: Message):
    await message.reply_text(
        START_TEXT,
        reply_markup=_main_keyboard(),
        parse_mode="html",
    )
    log.info(f"/start → {message.from_user.id}")


# ══════════════════════════════════════════════════════════════════════════════
#  HOME CALLBACK  (used by Help, Config etc. to come back)
# ══════════════════════════════════════════════════════════════════════════════

@app.on_callback_query(filters.regex("^menu_home$"))
async def cb_menu_home(client: Client, cq: CallbackQuery):
    await cq.answer()
    try:
        await cq.message.edit_text(
            START_TEXT,
            reply_markup=_main_keyboard(),
            parse_mode="html",
        )
    except Exception:
        pass


# ══════════════════════════════════════════════════════════════════════════════
#  GROUP STATS CALLBACK
# ══════════════════════════════════════════════════════════════════════════════

@app.on_callback_query(filters.regex("^menu_stats$"))
async def cb_menu_stats(client: Client, cq: CallbackQuery):
    await cq.answer()
    try:
        count = await get_waifu_count()
    except Exception:
        count = "N/A"

    chat = cq.message.chat
    is_group = chat.type in ("group", "supergroup")

    if is_group:
        try:
            members = await client.get_chat_members_count(chat.id)
        except Exception:
            members = "N/A"

        text = (
            f"📊 <b>Group Stats</b>\n\n"
            f"👥 <b>Members:</b>  <code>{members}</code>\n"
            f"🖼 <b>Total Waifus (DB):</b>  <code>{count}</code>\n"
            f"🏷 <b>Group:</b>  {chat.title}\n"
        )
    else:
        text = (
            f"📊 <b>Bot Stats</b>\n\n"
            f"🖼 <b>Total Waifus (DB):</b>  <code>{count}</code>\n"
        )

    await cq.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🏠 Home", callback_data="menu_home")],
        ]),
        parse_mode="html",
    )
  
