from pyrogram import enums
"""
WAIFUSCRPER — tools/help.py
Handles:
  • /help command
  • menu_help callback (start.py ke Home button se)
  • Category-wise guide with inline navigation
"""

from pyrogram import Client, filters
from pyrogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)

from WAIFUSCRPER import app
from WAIFUSCRPER.Logging import LOGGER

log = LOGGER(__name__)

# ══════════════════════════════════════════════════════════════════════════════
#  HELP CONTENT
# ══════════════════════════════════════════════════════════════════════════════

HELP_SECTIONS = {

    "main": {
        "text": (
            "❓ <b>WAIFUSCRPER — Help Guide</b>\n\n"
            "Niche se category chunlo:"
        ),
        "buttons": [
            [
                InlineKeyboardButton("🤖 Basic Commands",  callback_data="help_basic"),
                InlineKeyboardButton("👑 Admin Commands",  callback_data="help_admin"),
            ],
            [
                InlineKeyboardButton("⚙️ Config Guide",    callback_data="help_config"),
                InlineKeyboardButton("📥 Scraper Guide",   callback_data="help_scraper"),
            ],
            [
                InlineKeyboardButton("🔐 Session Guide",   callback_data="help_session"),
            ],
            [
                InlineKeyboardButton("🏠 Home",            callback_data="menu_home"),
            ],
        ],
    },

    "basic": {
        "text": (
            "🤖 <b>Basic Commands</b>\n\n"

            "/start\n"
            "┗ Bot ka main menu kholta hai.\n\n"

            "/help\n"
            "┗ Yeh guide dikhata hai.\n\n"

            "/cancel\n"
            "┗ Koi bhi chal raha setup (jaise string session) band kar deta hai.\n\n"

            "/setsession\n"
            "┗ String session setup shuru karta hai.\n"
            "┗ Phone → OTP → 2FA (agar laga ho) → Done.\n"
            "┗ 120 second ka timeout hai har step pe.\n\n"
        ),
        "buttons": [
            [
                InlineKeyboardButton("⬅️ Back",  callback_data="help_main"),
                InlineKeyboardButton("🏠 Home",  callback_data="menu_home"),
            ],
        ],
    },

    "admin": {
        "text": (
            "👑 <b>Admin / Sudo Commands</b>\n\n"
            "<i>Sirf Owner use kar sakta hai:</i>\n\n"

            "/addsudo &lt;user_id&gt;\n"
            "┗ Kisi ko sudo access deta hai.\n"
            "┗ Reply karke bhi use kar sakte ho.\n\n"

            "/rmsudo &lt;user_id&gt;\n"
            "┗ Kisi ka sudo access hata deta hai.\n"
            "┗ Owner ko remove nahi kar sakte.\n\n"

            "/sudolist\n"
            "┗ Saare sudo users ki list dikhata hai.\n\n"

            "<i>Sudo users config se nahi, DB se load hote hain.</i>\n"
        ),
        "buttons": [
            [
                InlineKeyboardButton("⬅️ Back",  callback_data="help_main"),
                InlineKeyboardButton("🏠 Home",  callback_data="menu_home"),
            ],
        ],
    },

    "config": {
        "text": (
            "⚙️ <b>Config Guide</b>\n\n"
            "/start → <b>Config</b> button press karo.\n\n"

            "📋 <b>Page 1 — Setup</b>\n"
            "┣ <b>Set Logger</b> — Log group/channel ID set karo\n"
            "┣ <b>Set Approve Mode</b> — On/Off karo approve system\n"
            "┣ <b>Set String Session</b> — Userbot login karo\n"
            "┣ <b>Set Caption Keyword</b> — Rarity keyword set karo\n"
            "┗ <b>Set Collection Name</b> — MongoDB collection naam\n\n"

            "📋 <b>Page 2 — Remove / Target</b>\n"
            "┣ <b>Remove String Session</b> — Session hata do\n"
            "┣ <b>Remove Logger</b> — Logger hata do\n"
            "┣ <b>Remove Collection</b> — DB collection naam hata do\n"
            "┣ <b>Remove Waifu by ID</b> — Specific waifu delete karo\n"
            "┣ <b>Set Target Channel</b> — Jis channel se scrape karna\n"
            "┣ <b>Fetch All Waifus</b> — Poora channel scan karo\n"
            "┗ <b>Set Keyboard Message</b> — Custom message set karo\n"
        ),
        "buttons": [
            [
                InlineKeyboardButton("⬅️ Back",  callback_data="help_main"),
                InlineKeyboardButton("🏠 Home",  callback_data="menu_home"),
            ],
        ],
    },

    "scraper": {
        "text": (
            "📥 <b>Scraper Guide</b>\n\n"

            "<b>Kaise kaam karta hai:</b>\n\n"

            "1️⃣ <b>Config mein Target Channel set karo</b>\n"
            "┗ Jis channel se waifus scrape karne hain.\n\n"

            "2️⃣ <b>String Session set karo</b>\n"
            "┗ Userbot us channel mein join karega.\n\n"

            "3️⃣ <b>Fetch All Waifus</b> karo Config se\n"
            "┗ Poora channel scan hoga, ek ek message process hoga.\n\n"

            "4️⃣ <b>Caption parsing:</b>\n"
            "┗ Waifu ID, Name, Rarity, Series, Added By — sab nikalta hai.\n"
            "┗ Agar caption mein ID nahi — auto-generate hoti hai.\n\n"

            "5️⃣ <b>Image upload:</b>\n"
            "┗ Catbox pe upload hoti hai (primary).\n"
            "┗ Fail ho toh ImgBB pe (fallback).\n\n"

            "6️⃣ <b>MongoDB mein save:</b>\n"
            "<code>{ name, img_url, rarity, series,\n"
            "  waifu_id, added_by, Date, event_tag }</code>\n\n"

            "⚡ <b>Auto Fetch New:</b>\n"
            "┗ Config se On/Off — naye waifus aate hi capture karta hai.\n\n"

            "✅ <b>Approve Mode:</b>\n"
            "┗ On → Logger group mein approve manga.\n"
            "┗ Off → Auto save.\n"
        ),
        "buttons": [
            [
                InlineKeyboardButton("⬅️ Back",  callback_data="help_main"),
                InlineKeyboardButton("🏠 Home",  callback_data="menu_home"),
            ],
        ],
    },

    "session": {
        "text": (
            "🔐 <b>String Session Guide</b>\n\n"

            "<b>String session kya hai?</b>\n"
            "┗ Userbot (tera Telegram account) bot ko channel "
            "join karne aur messages read karne deta hai.\n\n"

            "<b>Setup kaise karo:</b>\n\n"
            "1️⃣ Config → <b>Set String Session</b> dabao\n"
            "   ya seedha /setsession likho.\n\n"
            "2️⃣ <b>Phone number</b> bhejo (+91XXXXXXXXXX)\n\n"
            "3️⃣ Telegram se aaya <b>OTP</b> bhejo\n"
            "   (spaces ke saath, jaise Telegram bhejta hai)\n\n"
            "4️⃣ Agar <b>2FA laga hai</b> → password bhi mangega\n\n"
            "5️⃣ Session DB mein save ho jayegi ✅\n\n"

            "⚠️ <b>Dhyan rakh:</b>\n"
            "┣ Har step pe <b>120 second</b> ka timeout hai.\n"
            "┣ Beech mein /cancel likhke band kar sakte ho.\n"
            "┗ Session DB mein save hai — dobara set karne ki "
            "zarurat nahi jab tak remove na karo.\n"
        ),
        "buttons": [
            [
                InlineKeyboardButton("⬅️ Back",  callback_data="help_main"),
                InlineKeyboardButton("🏠 Home",  callback_data="menu_home"),
            ],
        ],
    },
}


# ══════════════════════════════════════════════════════════════════════════════
#  HELPERS
# ══════════════════════════════════════════════════════════════════════════════

def _build(section: str) -> tuple[str, InlineKeyboardMarkup]:
    data = HELP_SECTIONS[section]
    return data["text"], InlineKeyboardMarkup(data["buttons"])


# ══════════════════════════════════════════════════════════════════════════════
#  /help COMMAND
# ══════════════════════════════════════════════════════════════════════════════

@app.on_message(filters.command("help") & (filters.private | filters.group), group=0)
async def help_cmd(client: Client, message: Message):
    text, markup = _build("main")
    await message.reply_text(text, reply_markup=markup, parse_mode=enums.ParseMode.HTML)
    log.info(f"/help → {message.from_user.id}")


# ══════════════════════════════════════════════════════════════════════════════
#  CALLBACKS
# ══════════════════════════════════════════════════════════════════════════════

@app.on_callback_query(filters.regex("^menu_help$"), group=0)
async def cb_menu_help(client: Client, cq: CallbackQuery):
    await cq.answer()
    text, markup = _build("main")
    await cq.message.edit_text(text, reply_markup=markup, parse_mode=enums.ParseMode.HTML)


@app.on_callback_query(filters.regex("^help_(.+)$"), group=0)
async def cb_help_section(client: Client, cq: CallbackQuery):
    section = cq.matches[0].group(1)   # e.g. "basic", "admin", "config" …

    if section not in HELP_SECTIONS:
        return await cq.answer("Section nahi mila!", show_alert=True)

    await cq.answer()
    text, markup = _build(section)

    try:
        await cq.message.edit_text(text, reply_markup=markup, parse_mode=enums.ParseMode.HTML)
    except Exception:
        pass   # Message same hone pe Telegram error deta hai — ignore

