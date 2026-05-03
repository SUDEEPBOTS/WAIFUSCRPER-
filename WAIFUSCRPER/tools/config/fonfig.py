"""
WAIFUSCRPER — tools/config/Config.py
Full config panel with 3 pages of buttons.

Page 1 (Setup):
  Set Logger | Set Approve Mode | Set String Session
  Set Caption Keyword | Set Collection Name

Page 2 (Remove / Target):
  Remove String Session | Remove Logger | Remove Collection Name
  Remove Waifu by ID | Set Target Channel | Fetch All Waifus
  Set Keyboard Message

Page 3 (Auto Fetch):
  Auto Fetch New Waifus ON/OFF | Back to Home
"""

import asyncio

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
from WAIFUSCRPER.Database import (
    set_logger, get_logger, remove_logger,
    set_approve_mode, get_approve_mode,
    set_string_session, get_string_session, remove_string_session,
    set_collection_name, get_collection_name, remove_collection_name,
    set_target_channel, get_target_channel, remove_target_channel,
    set_auto_fetch, get_auto_fetch,
    set_keyboard_message, get_keyboard_message,
    remove_waifu_by_id, get_waifu_count,
)

log = LOGGER(__name__)

# ══════════════════════════════════════════════════════════════════════════════
#  AUTH CHECK
# ══════════════════════════════════════════════════════════════════════════════

def _is_owner(user_id: int) -> bool:
    return user_id == config.OWNER_ID

def _is_authorized(user_id: int) -> bool:
    return user_id == config.OWNER_ID or user_id in config.SUDO_USERS


# ══════════════════════════════════════════════════════════════════════════════
#  KEYBOARDS
# ══════════════════════════════════════════════════════════════════════════════

def _kb_p1() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📋 Set Logger",          callback_data="cfg_set_logger"),
            InlineKeyboardButton("✅ Set Approve Mode",    callback_data="cfg_set_approve"),
        ],
        [
            InlineKeyboardButton("🔐 Set String Session",  callback_data="cfg_set_session"),
        ],
        [
            InlineKeyboardButton("🔑 Set Caption Keyword", callback_data="cfg_set_keyword"),
            InlineKeyboardButton("🗂 Set Collection",      callback_data="cfg_set_collection"),
        ],
        [
            InlineKeyboardButton("🏠 Home", callback_data="menu_home"),
            InlineKeyboardButton("Next ▶️", callback_data="menu_config_p2"),
        ],
    ])


def _kb_p2() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🗑 Remove Session",      callback_data="cfg_rm_session"),
            InlineKeyboardButton("🗑 Remove Logger",       callback_data="cfg_rm_logger"),
        ],
        [
            InlineKeyboardButton("🗑 Remove Collection",   callback_data="cfg_rm_collection"),
            InlineKeyboardButton("🗑 Remove Waifu by ID",  callback_data="cfg_rm_waifu"),
        ],
        [
            InlineKeyboardButton("📡 Set Target Channel",  callback_data="cfg_set_target"),
            InlineKeyboardButton("📥 Fetch All Waifus",    callback_data="cfg_fetch_all"),
        ],
        [
            InlineKeyboardButton("💬 Set Keyboard Msg",    callback_data="cfg_set_keymsg"),
        ],
        [
            InlineKeyboardButton("◀️ Back", callback_data="menu_config_p1"),
            InlineKeyboardButton("🏠 Home", callback_data="menu_home"),
            InlineKeyboardButton("Next ▶️", callback_data="menu_config_p3"),
        ],
    ])


def _kb_p3() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🔄 Toggle Auto Fetch",   callback_data="cfg_toggle_autofetch"),
        ],
        [
            InlineKeyboardButton("◀️ Back", callback_data="menu_config_p2"),
            InlineKeyboardButton("🏠 Home", callback_data="menu_home"),
        ],
    ])

def _kb_home() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🏠 Home", callback_data="menu_home")],
    ])

def _kb_cancel() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("❌ Cancel", callback_data="cfg_cancel_input")],
    ])


# ══════════════════════════════════════════════════════════════════════════════
#  PAGE DISPLAYS
# ══════════════════════════════════════════════════════════════════════════════

async def _show_p1(msg_or_cq):
    text = (
        "⚙️ <b>Config — Page 1 (Setup)</b>\n\n"
        "Niche se jo setting karna ho wo dabao:"
    )
    if isinstance(msg_or_cq, CallbackQuery):
        await msg_or_cq.message.edit_text(text, reply_markup=_kb_p1(), parse_mode="html")
    else:
        await msg_or_cq.reply_text(text, reply_markup=_kb_p1(), parse_mode="html")


async def _show_p2(cq: CallbackQuery):
    text = (
        "⚙️ <b>Config — Page 2 (Remove / Target)</b>\n\n"
        "Niche se option chunlo:"
    )
    await cq.message.edit_text(text, reply_markup=_kb_p2(), parse_mode="html")


async def _show_p3(cq: CallbackQuery):
    auto = await get_auto_fetch()
    status = "🟢 ON" if auto else "🔴 OFF"
    text = (
        f"⚙️ <b>Config — Page 3 (Auto Fetch)</b>\n\n"
        f"🔄 <b>Auto Fetch New Waifus:</b>  {status}\n\n"
        "Button dabao toggle karne ke liye:"
    )
    await cq.message.edit_text(text, reply_markup=_kb_p3(), parse_mode="html")


# ══════════════════════════════════════════════════════════════════════════════
#  /config COMMAND + PAGE CALLBACKS
# ══════════════════════════════════════════════════════════════════════════════

@app.on_message(filters.command("config") & filters.private)
async def cmd_config(client: Client, message: Message):
    if not _is_authorized(message.from_user.id):
        return await message.reply_text("🚫 Permission nahi hai!", parse_mode="html")
    await _show_p1(message)


@app.on_callback_query(filters.regex("^menu_config_p1$"))
async def cb_config_p1(client: Client, cq: CallbackQuery):
    if not _is_authorized(cq.from_user.id):
        return await cq.answer("🚫 Permission nahi!", show_alert=True)
    await cq.answer()
    await _show_p1(cq)


@app.on_callback_query(filters.regex("^menu_config_p2$"))
async def cb_config_p2(client: Client, cq: CallbackQuery):
    if not _is_authorized(cq.from_user.id):
        return await cq.answer("🚫 Permission nahi!", show_alert=True)
    await cq.answer()
    await _show_p2(cq)


@app.on_callback_query(filters.regex("^menu_config_p3$"))
async def cb_config_p3(client: Client, cq: CallbackQuery):
    if not _is_authorized(cq.from_user.id):
        return await cq.answer("🚫 Permission nahi!", show_alert=True)
    await cq.answer()
    await _show_p3(cq)


# ══════════════════════════════════════════════════════════════════════════════
#  AWAITING INPUT STATE  {user_id: "state"}
# ══════════════════════════════════════════════════════════════════════════════

_awaiting: dict[int, str] = {}


@app.on_callback_query(filters.regex("^cfg_cancel_input$"))
async def cb_cancel_input(client: Client, cq: CallbackQuery):
    _awaiting.pop(cq.from_user.id, None)
    await cq.answer("Cancelled ✅")
    await _show_p1(cq)


# ── Generic text listener for all config inputs ────────────────────────────────

@app.on_message(filters.private & filters.text & ~filters.command(
    ["start","help","config","wstart","wstop","addsudo","rmsudo","sudolist","setsession","cancel"]
))
async def cfg_text_listener(client: Client, message: Message):
    uid   = message.from_user.id
    state = _awaiting.get(uid)
    if not state:
        return

    text = message.text.strip()
    _awaiting.pop(uid, None)

    # ── SET LOGGER ─────────────────────────────────────────────────────────────
    if state == "set_logger":
        try:
            chat_id = int(text)
            await set_logger(chat_id)
            await message.reply_text(
                f"✅ <b>Logger set!</b>\n<code>{chat_id}</code>",
                reply_markup=_kb_home(), parse_mode="html",
            )
        except ValueError:
            await message.reply_text(
                "❌ Sirf numeric Chat ID dalo! (e.g. -100xxxxxxxxxx)",
                reply_markup=_kb_home(), parse_mode="html",
            )

    # ── SET COLLECTION ─────────────────────────────────────────────────────────
    elif state == "set_collection":
        await set_collection_name(text)
        await message.reply_text(
            f"✅ <b>Collection name set:</b>  <code>{text}</code>",
            reply_markup=_kb_home(), parse_mode="html",
        )

    # ── SET CAPTION KEYWORD ────────────────────────────────────────────────────
    elif state == "set_keyword":
        # Save to DB as a config key
        from WAIFUSCRPER.Database.Mangodb import _set_config
        await _set_config("rarity_keyword", text)
        await message.reply_text(
            f"✅ <b>Caption keyword set:</b>  <code>{text}</code>",
            reply_markup=_kb_home(), parse_mode="html",
        )

    # ── SET TARGET CHANNEL ─────────────────────────────────────────────────────
    elif state == "set_target":
        try:
            # Accept numeric ID or @username
            try:
                val = int(text)
            except ValueError:
                val = text  # username string
            await set_target_channel(val)
            await message.reply_text(
                f"✅ <b>Target channel set:</b>  <code>{val}</code>",
                reply_markup=_kb_home(), parse_mode="html",
            )
        except Exception as e:
            await message.reply_text(
                f"❌ Error: <code>{e}</code>",
                reply_markup=_kb_home(), parse_mode="html",
            )

    # ── REMOVE WAIFU BY ID ─────────────────────────────────────────────────────
    elif state == "rm_waifu":
        deleted = await remove_waifu_by_id(text)
        if deleted:
            await message.reply_text(
                f"✅ <b>Waifu deleted!</b>  ID: <code>{text}</code>",
                reply_markup=_kb_home(), parse_mode="html",
            )
        else:
            await message.reply_text(
                f"❌ <b>Waifu not found.</b>  ID: <code>{text}</code>",
                reply_markup=_kb_home(), parse_mode="html",
            )

    # ── SET KEYBOARD MESSAGE ───────────────────────────────────────────────────
    elif state == "set_keymsg":
        await set_keyboard_message(text)
        await message.reply_text(
            f"✅ <b>Keyboard message set!</b>\n\n{text}",
            reply_markup=_kb_home(), parse_mode="html",
        )


# ══════════════════════════════════════════════════════════════════════════════
#  INDIVIDUAL CONFIG BUTTON CALLBACKS
# ══════════════════════════════════════════════════════════════════════════════

# ── Set Logger ─────────────────────────────────────────────────────────────────

@app.on_callback_query(filters.regex("^cfg_set_logger$"))
async def cb_set_logger(client: Client, cq: CallbackQuery):
    if not _is_authorized(cq.from_user.id):
        return await cq.answer("🚫 Permission nahi!", show_alert=True)
    await cq.answer()
    _awaiting[cq.from_user.id] = "set_logger"
    current = await get_logger()
    await cq.message.edit_text(
        f"📋 <b>Set Logger</b>\n\n"
        f"Current: <code>{current or 'Not set'}</code>\n\n"
        "Log group/channel ka <b>numeric ID</b> bhejo:\n"
        "<i>(e.g. -100xxxxxxxxxx)</i>",
        reply_markup=_kb_cancel(), parse_mode="html",
    )


# ── Set Approve Mode ───────────────────────────────────────────────────────────

@app.on_callback_query(filters.regex("^cfg_set_approve$"))
async def cb_set_approve(client: Client, cq: CallbackQuery):
    if not _is_authorized(cq.from_user.id):
        return await cq.answer("🚫 Permission nahi!", show_alert=True)
    await cq.answer()
    current = await get_approve_mode()
    new_val = not current
    await set_approve_mode(new_val)
    status = "🟢 ON" if new_val else "🔴 OFF"
    await cq.message.edit_text(
        f"✅ <b>Approve Mode:</b>  {status}\n\n"
        "<i>Waifu scraping pe har waifu approve karna hoga.</i>",
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton("🔄 Toggle Again", callback_data="cfg_set_approve"),
                InlineKeyboardButton("🏠 Home",         callback_data="menu_home"),
            ],
        ]),
        parse_mode="html",
    )


# ── Set String Session (redirects to /setsession flow) ────────────────────────

@app.on_callback_query(filters.regex("^cfg_set_session$"))
async def cb_set_session(client: Client, cq: CallbackQuery):
    if not _is_authorized(cq.from_user.id):
        return await cq.answer("🚫 Permission nahi!", show_alert=True)
    await cq.answer()
    await cq.message.edit_text(
        "🔐 <b>String Session Setup</b>\n\n"
        "Private mein /setsession bhejo ya yahan seedha type karo.\n\n"
        "<i>Yeh flow shuru karega:\n"
        "Phone → OTP → 2FA (agar ho) → Done</i>",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("▶️ Shuru Karo", callback_data="cfg_start_session_flow")],
            [InlineKeyboardButton("🏠 Home",       callback_data="menu_home")],
        ]),
        parse_mode="html",
    )


@app.on_callback_query(filters.regex("^cfg_start_session_flow$"))
async def cb_start_session_flow(client: Client, cq: CallbackQuery):
    if not _is_authorized(cq.from_user.id):
        return await cq.answer("🚫 Permission nahi!", show_alert=True)
    await cq.answer()
    # Trigger the /setsession command handler
    await cq.message.reply_text(
        "✅ <b>/setsession</b> type karo is chat mein session setup ke liye.",
        parse_mode="html",
    )


# ── Set Caption Keyword ────────────────────────────────────────────────────────

@app.on_callback_query(filters.regex("^cfg_set_keyword$"))
async def cb_set_keyword(client: Client, cq: CallbackQuery):
    if not _is_authorized(cq.from_user.id):
        return await cq.answer("🚫 Permission nahi!", show_alert=True)
    await cq.answer()
    _awaiting[cq.from_user.id] = "set_keyword"
    await cq.message.edit_text(
        "🔑 <b>Set Caption Keyword</b>\n\n"
        "Default: <code>Rarity</code>\n\n"
        "Caption mein rarity dhundne ka keyword bhejo:\n"
        "<i>(Jo label waifu caption mein use hota hai)</i>",
        reply_markup=_kb_cancel(), parse_mode="html",
    )


# ── Set Collection Name ────────────────────────────────────────────────────────

@app.on_callback_query(filters.regex("^cfg_set_collection$"))
async def cb_set_collection(client: Client, cq: CallbackQuery):
    if not _is_authorized(cq.from_user.id):
        return await cq.answer("🚫 Permission nahi!", show_alert=True)
    await cq.answer()
    _awaiting[cq.from_user.id] = "set_collection"
    current = await get_collection_name()
    await cq.message.edit_text(
        f"🗂 <b>Set Collection Name</b>\n\n"
        f"Current: <code>{current or 'waifus (default)'}</code>\n\n"
        "MongoDB collection ka naam bhejo:",
        reply_markup=_kb_cancel(), parse_mode="html",
    )


# ── Remove String Session ──────────────────────────────────────────────────────

@app.on_callback_query(filters.regex("^cfg_rm_session$"))
async def cb_rm_session(client: Client, cq: CallbackQuery):
    if not _is_authorized(cq.from_user.id):
        return await cq.answer("🚫 Permission nahi!", show_alert=True)
    await cq.answer()
    await remove_string_session()
    await cq.message.edit_text(
        "✅ <b>String Session remove kar diya!</b>\n\n"
        "Dobara set karne ke liye /setsession use karo.",
        reply_markup=_kb_home(), parse_mode="html",
    )


# ── Remove Logger ──────────────────────────────────────────────────────────────

@app.on_callback_query(filters.regex("^cfg_rm_logger$"))
async def cb_rm_logger(client: Client, cq: CallbackQuery):
    if not _is_authorized(cq.from_user.id):
        return await cq.answer("🚫 Permission nahi!", show_alert=True)
    await cq.answer()
    await remove_logger()
    await cq.message.edit_text(
        "✅ <b>Logger remove kar diya!</b>",
        reply_markup=_kb_home(), parse_mode="html",
    )


# ── Remove Collection ──────────────────────────────────────────────────────────

@app.on_callback_query(filters.regex("^cfg_rm_collection$"))
async def cb_rm_collection(client: Client, cq: CallbackQuery):
    if not _is_authorized(cq.from_user.id):
        return await cq.answer("🚫 Permission nahi!", show_alert=True)
    await cq.answer()
    await remove_collection_name()
    await cq.message.edit_text(
        "✅ <b>Collection name remove kar diya!</b>\n"
        "<i>Default 'waifus' use hoga ab.</i>",
        reply_markup=_kb_home(), parse_mode="html",
    )


# ── Remove Waifu by ID ─────────────────────────────────────────────────────────

@app.on_callback_query(filters.regex("^cfg_rm_waifu$"))
async def cb_rm_waifu(client: Client, cq: CallbackQuery):
    if not _is_authorized(cq.from_user.id):
        return await cq.answer("🚫 Permission nahi!", show_alert=True)
    await cq.answer()
    _awaiting[cq.from_user.id] = "rm_waifu"
    await cq.message.edit_text(
        "🗑 <b>Remove Waifu by ID</b>\n\n"
        "Waifu ka <b>waifu_id</b> bhejo jo delete karna hai:",
        reply_markup=_kb_cancel(), parse_mode="html",
    )


# ── Set Target Channel ─────────────────────────────────────────────────────────

@app.on_callback_query(filters.regex("^cfg_set_target$"))
async def cb_set_target(client: Client, cq: CallbackQuery):
    if not _is_authorized(cq.from_user.id):
        return await cq.answer("🚫 Permission nahi!", show_alert=True)
    await cq.answer()
    _awaiting[cq.from_user.id] = "set_target"
    current = await get_target_channel()
    await cq.message.edit_text(
        f"📡 <b>Set Target Channel</b>\n\n"
        f"Current: <code>{current or 'Not set'}</code>\n\n"
        "Channel ID ya @username bhejo\n"
        "<i>Jis channel se waifus scrape karne hain.</i>",
        reply_markup=_kb_cancel(), parse_mode="html",
    )


# ── Fetch All Waifus (redirect to /wstart) ────────────────────────────────────

@app.on_callback_query(filters.regex("^cfg_fetch_all$"))
async def cb_fetch_all(client: Client, cq: CallbackQuery):
    if not _is_authorized(cq.from_user.id):
        return await cq.answer("🚫 Permission nahi!", show_alert=True)
    await cq.answer()

    target = await get_target_channel()
    count  = await get_waifu_count()

    if not target:
        return await cq.message.edit_text(
            "❌ <b>Target Channel set nahi hai!</b>\n"
            "Pehle Config → Set Target Channel karo.",
            reply_markup=_kb_home(), parse_mode="html",
        )

    await cq.message.edit_text(
        f"📥 <b>Fetch All Waifus</b>\n\n"
        f"📡 <b>Target:</b>  <code>{target}</code>\n"
        f"🖼 <b>DB mein abhi:</b>  <code>{count}</code> waifus\n\n"
        "Scraping shuru karne ke liye <b>/wstart</b> bhejo.",
        reply_markup=_kb_home(), parse_mode="html",
    )


# ── Set Keyboard Message ───────────────────────────────────────────────────────

@app.on_callback_query(filters.regex("^cfg_set_keymsg$"))
async def cb_set_keymsg(client: Client, cq: CallbackQuery):
    if not _is_authorized(cq.from_user.id):
        return await cq.answer("🚫 Permission nahi!", show_alert=True)
    await cq.answer()
    _awaiting[cq.from_user.id] = "set_keymsg"
    current = await get_keyboard_message()
    await cq.message.edit_text(
        f"💬 <b>Set Keyboard Message</b>\n\n"
        f"Current:\n<code>{current or 'Not set'}</code>\n\n"
        "Naya message bhejo:",
        reply_markup=_kb_cancel(), parse_mode="html",
    )


# ── Toggle Auto Fetch ──────────────────────────────────────────────────────────

@app.on_callback_query(filters.regex("^cfg_toggle_autofetch$"))
async def cb_toggle_autofetch(client: Client, cq: CallbackQuery):
    if not _is_authorized(cq.from_user.id):
        return await cq.answer("🚫 Permission nahi!", show_alert=True)
    await cq.answer()
    current = await get_auto_fetch()
    new_val = not current
    await set_auto_fetch(new_val)
    status = "🟢 ON" if new_val else "🔴 OFF"
    await cq.message.edit_text(
        f"🔄 <b>Auto Fetch New Waifus:</b>  {status}\n\n"
        "<i>Naye waifus channel pe aate hi auto capture honge.</i>",
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton("🔄 Toggle Again", callback_data="cfg_toggle_autofetch"),
                InlineKeyboardButton("◀️ Back",         callback_data="menu_config_p3"),
            ],
            [InlineKeyboardButton("🏠 Home", callback_data="menu_home")],
        ]),
        parse_mode="html",
  )
