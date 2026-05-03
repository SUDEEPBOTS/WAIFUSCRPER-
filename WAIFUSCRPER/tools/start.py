from pyrogram import Client, filters, enums
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

START_TEXT = (
    "🌸 <b>ᴡᴀɪꜰᴜsᴄʀᴘᴇʀ</b> — ʏᴏᴜʀ ᴡᴀɪꜰᴜ ᴄᴏʟʟᴇᴄᴛɪᴏɴ ʙᴏᴛ!\n\n"
    "━━━━━━━━━━━━━━━━━━━━━\n"
    "🤖 ϻᴀιη ғєᴀᴛᴜʀєs:\n"
    "  • sᴄʀᴀᴘє ᴡᴀɪғᴜs ғʀᴏϻ ᴛєʟєɢʀᴀϻ ᴄʜᴀηηєʟs\n"
    "  • ᴀᴘᴘʀᴏᴠє / ᴀᴜᴛᴏ ϻᴏᴅє\n"
    "  • sᴀᴠє ᴛᴏ ϻᴏηɢᴏᴅʙ\n"
    "  • ᴄᴀᴛʙᴏx + ιϻɢʙʙ ιϻᴀɢє ʜᴏsᴛιηɢ\n"
    "━━━━━━━━━━━━━━━━━━━━━\n\n"
    "choose an option below 👇"
)


def _main_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("˹ 𝐂ᴏηғιɢ ˼",  callback_data="menu_config_p1"),
            InlineKeyboardButton("˹ 𝚮єʟᴘ ˼",    callback_data="menu_help"),
        ],
        [
            InlineKeyboardButton("˹ 𝐒ᴛᴀᴛs ˼",   callback_data="menu_stats"),
        ],
    ])


@app.on_message(filters.command("start") & (filters.private | filters.group), group=0)
async def cmd_start(client: Client, message: Message):
    try:
        await message.reply_text(
            START_TEXT,
            reply_markup=_main_keyboard(),
            parse_mode=enums.ParseMode.HTML,
        )
        log.info(f"/start → {message.from_user.id}")
    except Exception as e:
        log.error(f"/start error: {e}")


@app.on_callback_query(filters.regex("^menu_home$"), group=0)
async def cb_menu_home(client: Client, cq: CallbackQuery):
    await cq.answer()
    try:
        await cq.message.edit_text(
            START_TEXT,
            reply_markup=_main_keyboard(),
            parse_mode=enums.ParseMode.HTML,
        )
    except Exception as e:
        log.error(f"menu_home error: {e}")


@app.on_callback_query(filters.regex("^menu_stats$"), group=0)
async def cb_menu_stats(client: Client, cq: CallbackQuery):
    await cq.answer()
    try:
        count = await get_waifu_count()
    except Exception:
        count = "n/a"

    chat = cq.message.chat
    is_group = chat.type in ("group", "supergroup")

    if is_group:
        try:
            members = await client.get_chat_members_count(chat.id)
        except Exception:
            members = "n/a"
        text = (
            f"📊 <b>ɢʀᴏᴜᴘ sᴛᴀᴛs</b>\n\n"
            f"👥 <b>ϻєϻʙєʀs:</b>  <code>{members}</code>\n"
            f"🖼 <b>ᴛᴏᴛᴀʟ ᴡᴀɪғᴜs (ᴅʙ):</b>  <code>{count}</code>\n"
            f"🏷 <b>ɢʀᴏᴜᴘ:</b>  {chat.title}\n"
        )
    else:
        text = (
            f"📊 <b>ʙᴏᴛ sᴛᴀᴛs</b>\n\n"
            f"🖼 <b>ᴛᴏᴛᴀʟ ᴡᴀɪғᴜs (ᴅʙ):</b>  <code>{count}</code>\n"
        )

    try:
        await cq.message.edit_text(
            text,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("˹ 𝚮ᴏϻє ˼", callback_data="menu_home")],
            ]),
            parse_mode=enums.ParseMode.HTML,
        )
    except Exception as e:
        log.error(f"menu_stats error: {e}")
      
