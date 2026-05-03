from pyrogram import Client, filters, enums
from pyrogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)

from WAIFUSCRPER import app
from WAIFUSCRPER.Logging import LOGGER

log = LOGGER(__name__)

HELP_SECTIONS = {

    "main": {
        "text": (
            "❓ <b>waifuscrper — help guide</b>\n\n"
            "choose a category below:"
        ),
        "buttons": [
            [
                InlineKeyboardButton("˹ 𝐁ᴀsιᴄ 𝐂ᴏϻϻᴀηᴅs ˼",  callback_data="help_basic"),
                InlineKeyboardButton("˹ 𝐀ᴅϻιη 𝐂ᴏϻϻᴀηᴅs ˼",  callback_data="help_admin"),
            ],
            [
                InlineKeyboardButton("˹ 𝐂ᴏηғιɢ 𝚮ᴜιᴅє ˼",     callback_data="help_config"),
                InlineKeyboardButton("˹ 𝐒ᴄʀᴀᴘєʀ 𝚮ᴜιᴅє ˼",    callback_data="help_scraper"),
            ],
            [
                InlineKeyboardButton("˹ 𝐒єssιᴏη 𝚮ᴜιᴅє ˼",    callback_data="help_session"),
            ],
            [
                InlineKeyboardButton("˹ 𝚮ᴏϻє ˼",              callback_data="menu_home"),
            ],
        ],
    },

    "basic": {
        "text": (
            "🤖 <b>basic commands</b>\n\n"

            "/start\n"
            "┗ opens the bot's main menu.\n\n"

            "/help\n"
            "┗ shows this guide.\n\n"

            "/cancel\n"
            "┗ cancels any running setup (like string session).\n\n"

            "/setsession\n"
            "┗ starts string session setup.\n"
            "┗ phone → otp → 2fa (if enabled) → done.\n"
            "┗ 120 second timeout per step.\n\n"
        ),
        "buttons": [
            [
                InlineKeyboardButton("˹ 𝐁ᴀᴄᴋ ˼",  callback_data="help_main"),
                InlineKeyboardButton("˹ 𝚮ᴏϻє ˼",  callback_data="menu_home"),
            ],
        ],
    },

    "admin": {
        "text": (
            "👑 <b>admin / sudo commands</b>\n\n"
            "<i>owner only:</i>\n\n"

            "/addsudo &lt;user_id&gt;\n"
            "┗ grants sudo access to a user.\n"
            "┗ can also be used by replying to a message.\n\n"

            "/rmsudo &lt;user_id&gt;\n"
            "┗ removes sudo access from a user.\n"
            "┗ owner cannot be removed.\n\n"

            "/sudolist\n"
            "┗ shows the list of all sudo users.\n\n"

            "<i>sudo users are loaded from db, not config.</i>\n"
        ),
        "buttons": [
            [
                InlineKeyboardButton("˹ 𝐁ᴀᴄᴋ ˼",  callback_data="help_main"),
                InlineKeyboardButton("˹ 𝚮ᴏϻє ˼",  callback_data="menu_home"),
            ],
        ],
    },

    "config": {
        "text": (
            "⚙️ <b>config guide</b>\n\n"
            "/start → press the <b>config</b> button.\n\n"

            "📋 <b>page 1 — setup</b>\n"
            "┣ <b>set logger</b> — set log group/channel id\n"
            "┣ <b>set approve mode</b> — turn approve system on/off\n"
            "┣ <b>set string session</b> — login userbot\n"
            "┣ <b>set caption keyword</b> — set rarity keyword\n"
            "┗ <b>set collection name</b> — mongodb collection name\n\n"

            "📋 <b>page 2 — remove / target</b>\n"
            "┣ <b>remove string session</b> — delete session\n"
            "┣ <b>remove logger</b> — delete logger\n"
            "┣ <b>remove collection</b> — delete db collection name\n"
            "┣ <b>remove waifu by id</b> — delete a specific waifu\n"
            "┣ <b>set target channel</b> — channel to scrape from\n"
            "┣ <b>fetch all waifus</b> — scan entire channel\n"
            "┗ <b>set keyboard message</b> — set custom message\n"
        ),
        "buttons": [
            [
                InlineKeyboardButton("˹ 𝐁ᴀᴄᴋ ˼",  callback_data="help_main"),
                InlineKeyboardButton("˹ 𝚮ᴏϻє ˼",  callback_data="menu_home"),
            ],
        ],
    },

    "scraper": {
        "text": (
            "📥 <b>scraper guide</b>\n\n"

            "<b>how it works:</b>\n\n"

            "1️⃣ <b>set target channel in config</b>\n"
            "┗ the channel you want to scrape waifus from.\n\n"

            "2️⃣ <b>set string session</b>\n"
            "┗ userbot will join that channel.\n\n"

            "3️⃣ <b>fetch all waifus</b> from config\n"
            "┗ full channel scan, processes each message one by one.\n\n"

            "4️⃣ <b>caption parsing:</b>\n"
            "┗ extracts waifu id, name, rarity, series, added by.\n"
            "┗ if no id in caption — auto-generated.\n\n"

            "5️⃣ <b>image upload:</b>\n"
            "┗ uploads to catbox (primary).\n"
            "┗ falls back to imgbb if catbox fails.\n\n"

            "6️⃣ <b>saved to mongodb:</b>\n"
            "<code>{ name, img_url, rarity, series,\n"
            "  waifu_id, added_by, date, event_tag }</code>\n\n"

            "⚡ <b>auto fetch new:</b>\n"
            "┗ on/off from config — captures new waifus as they arrive.\n\n"

            "✅ <b>approve mode:</b>\n"
            "┗ on → asks for approval in logger group.\n"
            "┗ off → auto save.\n"
        ),
        "buttons": [
            [
                InlineKeyboardButton("˹ 𝐁ᴀᴄᴋ ˼",  callback_data="help_main"),
                InlineKeyboardButton("˹ 𝚮ᴏϻє ˼",  callback_data="menu_home"),
            ],
        ],
    },

    "session": {
        "text": (
            "🔐 <b>string session guide</b>\n\n"

            "<b>what is a string session?</b>\n"
            "┗ lets the userbot (your telegram account) join channels "
            "and read messages on behalf of the bot.\n\n"

            "<b>how to set it up:</b>\n\n"
            "1️⃣ config → press <b>set string session</b>\n"
            "   or just send /setsession.\n\n"
            "2️⃣ send your <b>phone number</b> (+91xxxxxxxxxx)\n\n"
            "3️⃣ send the <b>otp</b> from telegram\n"
            "   (spaces are fine, just as telegram sends it)\n\n"
            "4️⃣ if <b>2fa is enabled</b> → it will ask for password too\n\n"
            "5️⃣ session is saved to db ✅\n\n"

            "⚠️ <b>note:</b>\n"
            "┣ each step has a <b>120 second</b> timeout.\n"
            "┣ send /cancel anytime to abort.\n"
            "┗ session stays in db — no need to set again "
            "unless you remove it.\n"
        ),
        "buttons": [
            [
                InlineKeyboardButton("˹ 𝐁ᴀᴄᴋ ˼",  callback_data="help_main"),
                InlineKeyboardButton("˹ 𝚮ᴏϻє ˼",  callback_data="menu_home"),
            ],
        ],
    },
}


def _build(section: str) -> tuple[str, InlineKeyboardMarkup]:
    data = HELP_SECTIONS[section]
    return data["text"], InlineKeyboardMarkup(data["buttons"])


@app.on_message(filters.command("help") & (filters.private | filters.group), group=0)
async def help_cmd(client: Client, message: Message):
    text, markup = _build("main")
    await message.reply_text(text, reply_markup=markup, parse_mode=enums.ParseMode.HTML)
    log.info(f"/help → {message.from_user.id}")


@app.on_callback_query(filters.regex("^menu_help$"), group=0)
async def cb_menu_help(client: Client, cq: CallbackQuery):
    await cq.answer()
    text, markup = _build("main")
    await cq.message.edit_text(text, reply_markup=markup, parse_mode=enums.ParseMode.HTML)


@app.on_callback_query(filters.regex("^help_(.+)$"), group=0)
async def cb_help_section(client: Client, cq: CallbackQuery):
    section = cq.matches[0].group(1)

    if section not in HELP_SECTIONS:
        return await cq.answer("section not found!", show_alert=True)

    await cq.answer()
    text, markup = _build(section)

    try:
        await cq.message.edit_text(text, reply_markup=markup, parse_mode=enums.ParseMode.HTML)
    except Exception:
        pass
      
