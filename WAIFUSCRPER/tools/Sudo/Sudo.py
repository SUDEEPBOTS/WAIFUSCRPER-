"""
Sudo.py
• /addsudo <id>  — add sudo user
• /rmsudo <id>   — remove sudo user
• /sudolist      — list all sudos
• Config menu with inline session generation (phone → OTP → 2FA)
"""

import asyncio
from html import escape

from pyrogram import Client, enums, filters
from pyrogram.errors import (
    BadRequest,
    PhoneCodeExpired,
    PhoneCodeInvalid,
    SessionPasswordNeeded,
)
from pyrogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

import config
from WAIFUSCRPER import bot, start_userbot, stop_userbot
from WAIFUSCRPER.Database import (
    delete_waifu_by_id,
    get_config,
    set_config,
    unset_config,
    waifu_count,
    # Sudo DB helpers — defined below in Database/__init__.py
    add_sudo,
    remove_sudo,
    get_sudos,
)
from WAIFUSCRPER.logging import log

# ── Conversation states ───────────────────────────────────────────────────────
# user_id → {"state": str, ...extra data...}
_conv: dict[int, dict] = {}

# Temporary pyrogram client during session generation
# user_id → Client
_gen_clients: dict[int, Client] = {}

# Phone code hash during OTP flow
# user_id → {"phone": str, "hash": str, "client": Client}
_otp_sessions: dict[int, dict] = {}

INPUT_TIMEOUT = 180  # 3 min


# ── Keyboards ─────────────────────────────────────────────────────────────────

def _kb_home():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📋 Logger Channel",  callback_data="cfg:set_logger"),
            InlineKeyboardButton("✅ Approve Channel", callback_data="cfg:set_approve"),
        ],
        [
            InlineKeyboardButton("📱 String Session",  callback_data="cfg:set_session"),
            InlineKeyboardButton("📝 Set Caption",     callback_data="cfg:set_caption"),
        ],
        [
            InlineKeyboardButton("➡️ Next →", callback_data="cfg:page2"),
        ],
    ])


def _kb_page2():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📚 Collection Name",   callback_data="cfg:set_collection"),
        ],
        [
            InlineKeyboardButton("❌ Remove Session",    callback_data="cfg:rm_session"),
            InlineKeyboardButton("🗑 Remove Logger",     callback_data="cfg:rm_logger"),
        ],
        [
            InlineKeyboardButton("🗑 Remove Collection", callback_data="cfg:rm_collection"),
            InlineKeyboardButton("🗑 Remove Waifu ID",   callback_data="cfg:rm_waifu"),
        ],
        [
            InlineKeyboardButton("⬅️ Back", callback_data="cfg:page1"),
            InlineKeyboardButton("➡️ Next →", callback_data="cfg:page3"),
        ],
    ])


def _kb_page3(listener_on: bool = False):
    toggle_label = f"{'🟢' if listener_on else '🔴'} Live Listener: {'ON' if listener_on else 'OFF'}"
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📢 Set Target Channel", callback_data="cfg:set_target"),
        ],
        [
            InlineKeyboardButton("🔍 Fetch All Waifus",   callback_data="cfg:fetch_all"),
        ],
        [
            InlineKeyboardButton(toggle_label,            callback_data="cfg:toggle_listener"),
        ],
        [
            InlineKeyboardButton("⌨️ Keyboard Message",   callback_data="cfg:set_keyboard"),
        ],
        [
            InlineKeyboardButton("⬅️ Back to Home",       callback_data="cfg:page1"),
        ],
    ])


def _kb_start():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("⚙️ Config", callback_data="cfg:page1"),
            InlineKeyboardButton("❓ Help",    callback_data="cfg:help"),
        ],
    ])


def _kb_cancel():
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("❌ Cancel", callback_data="cfg:cancel_flow")
    ]])


# ── Permission check ──────────────────────────────────────────────────────────

async def _is_sudo(user_id: int) -> bool:
    sudos = await get_sudos()
    return user_id in sudos or user_id == config.OWNER_ID


# ── /start ────────────────────────────────────────────────────────────────────

@bot.on_message(filters.command("start") & filters.private)
async def start_cmd(_: Client, message: Message):
    user = message.from_user
    await message.reply_photo(
        photo="https://i.imgur.com/eGllAJO.jpeg",
        caption=(
            f"<blockquote>🌸 <b>WaifuScrper Bot</b></blockquote>\n\n"
            f"Konnichiwa, <b>{escape(user.first_name)}</b>~\n\n"
            f"I scrape waifus from your target channel,\n"
            f"handle approvals, and save them to MongoDB!\n\n"
            f"Use <b>⚙️ Config</b> to set everything up."
        ),
        parse_mode=enums.ParseMode.HTML,
        reply_markup=_kb_start(),
    )


# ── /addsudo ──────────────────────────────────────────────────────────────────

@bot.on_message(filters.command("addsudo") & filters.private)
async def addsudo_cmd(_: Client, message: Message):
    if message.from_user.id != config.OWNER_ID:
        return await message.reply_text("🚫 Owner only!")

    args = message.command
    # Accept: /addsudo 123456  OR reply to a user
    target_id = None

    if len(args) > 1:
        try:
            target_id = int(args[1])
        except ValueError:
            return await message.reply_text("❌ Invalid user ID.")

    elif message.reply_to_message:
        target_id = message.reply_to_message.from_user.id

    if not target_id:
        return await message.reply_text(
            "Usage:\n"
            "<code>/addsudo 123456</code>\n"
            "or reply to a user's message with <code>/addsudo</code>",
            parse_mode=enums.ParseMode.HTML,
        )

    if target_id == config.OWNER_ID:
        return await message.reply_text("👑 That's you bro — already owner!")

    await add_sudo(target_id)
    await message.reply_text(
        f"✅ <code>{target_id}</code> added as sudo!",
        parse_mode=enums.ParseMode.HTML,
    )
    log.info(f"[Sudo] {target_id} added by owner")


# ── /rmsudo ───────────────────────────────────────────────────────────────────

@bot.on_message(filters.command("rmsudo") & filters.private)
async def rmsudo_cmd(_: Client, message: Message):
    if message.from_user.id != config.OWNER_ID:
        return await message.reply_text("🚫 Owner only!")

    args = message.command
    target_id = None

    if len(args) > 1:
        try:
            target_id = int(args[1])
        except ValueError:
            return await message.reply_text("❌ Invalid user ID.")
    elif message.reply_to_message:
        target_id = message.reply_to_message.from_user.id

    if not target_id:
        return await message.reply_text(
            "Usage:\n"
            "<code>/rmsudo 123456</code>\n"
            "or reply to a user's message with <code>/rmsudo</code>",
            parse_mode=enums.ParseMode.HTML,
        )

    if target_id == config.OWNER_ID:
        return await message.reply_text("👑 Can't remove owner!")

    removed = await remove_sudo(target_id)
    if removed:
        await message.reply_text(
            f"✅ <code>{target_id}</code> removed from sudo.",
            parse_mode=enums.ParseMode.HTML,
        )
        log.info(f"[Sudo] {target_id} removed by owner")
    else:
        await message.reply_text(
            f"⚠️ <code>{target_id}</code> was not a sudo.",
            parse_mode=enums.ParseMode.HTML,
        )


# ── /sudolist ─────────────────────────────────────────────────────────────────

@bot.on_message(filters.command("sudolist") & filters.private)
async def sudolist_cmd(_: Client, message: Message):
    if not await _is_sudo(message.from_user.id):
        return await message.reply_text("🚫 Not authorized!")

    sudos = await get_sudos()
    lines = [f"👑 <code>{config.OWNER_ID}</code> — Owner"]
    for uid in sudos:
        if uid != config.OWNER_ID:
            lines.append(f"🛡 <code>{uid}</code> — Sudo")

    await message.reply_text(
        "<blockquote>🛡 <b>Sudo Users</b></blockquote>\n\n" + "\n".join(lines),
        parse_mode=enums.ParseMode.HTML,
    )


# ── /cancel ───────────────────────────────────────────────────────────────────

@bot.on_message(filters.command("cancel") & filters.private)
async def cancel_cmd(_: Client, message: Message):
    user_id = message.from_user.id
    await _cleanup_flow(user_id)
    await message.reply_text("❌ Cancelled.")


# ── Config callbacks ──────────────────────────────────────────────────────────

@bot.on_callback_query(filters.regex(r"^cfg:"))
async def config_callback(_: Client, query: CallbackQuery):
    if not await _is_sudo(query.from_user.id):
        return await query.answer("🚫 Not authorized!", show_alert=True)

    action  = query.data.split(":", 1)[1]
    user_id = query.from_user.id

    # ── Pages ─────────────────────────────────────────────────────────────────

    if action == "page1":
        cfg  = await get_config()
        text = await _config_status(cfg)
        await query.message.edit_text(
            text,
            parse_mode=enums.ParseMode.HTML,
            reply_markup=_kb_home(),
        )
        return await query.answer()

    if action == "page2":
        await query.message.edit_text(
            "⚙️ <b>Config — Page 2</b>",
            parse_mode=enums.ParseMode.HTML,
            reply_markup=_kb_page2(),
        )
        return await query.answer()

    if action == "page3":
        from WAIFUSCRPER.tools.dwonloder.Dwonlod import _listener_active
        cfg    = await get_config()
        count  = await waifu_count()
        target = cfg.get("target_channel", "Not set")
        await query.message.edit_text(
            f"⚙️ <b>Config — Page 3</b>\n\n"
            f"📢 Target   : <code>{target}</code>\n"
            f"🗂 Waifus   : <b>{count}</b> in DB\n"
            f"📡 Listener : <b>{'🟢 ON' if _listener_active else '🔴 OFF'}</b>",
            parse_mode=enums.ParseMode.HTML,
            reply_markup=_kb_page3(_listener_active),
        )
        return await query.answer()

    if action == "help":
        await query.message.edit_text(
            _help_text(),
            parse_mode=enums.ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("⬅️ Back", callback_data="cfg:page1")
            ]]),
        )
        return await query.answer()

    # ── Cancel active flow ────────────────────────────────────────────────────

    if action == "cancel_flow":
        await _cleanup_flow(user_id)
        await query.answer("❌ Cancelled.", show_alert=True)
        cfg  = await get_config()
        text = await _config_status(cfg)
        await query.message.edit_text(
            text,
            parse_mode=enums.ParseMode.HTML,
            reply_markup=_kb_home(),
        )
        return

    # ── String session — start phone flow ─────────────────────────────────────

    if action == "set_session":
        await _cleanup_flow(user_id)   # clear any old flow
        _conv[user_id] = {"state": "await_phone"}
        await query.message.reply_text(
            "📱 <b>Session Generator</b>\n\n"
            "Send your phone number with country code:\n"
            "<code>+91XXXXXXXXXX</code>\n\n"
            "<i>You have 3 minutes to respond.</i>",
            parse_mode=enums.ParseMode.HTML,
            reply_markup=_kb_cancel(),
        )
        # Start timeout
        asyncio.create_task(_flow_timeout(user_id, query.message.chat.id))
        return await query.answer()

    # ── Simple set fields ─────────────────────────────────────────────────────

    prompts = {
        "set_logger":     ("📋", "logger_channel",  "Send logger channel ID or @username:"),
        "set_approve":    ("✅", "approve_channel", "Send approval channel ID or @username:"),
        "set_caption":    ("📝", "caption_keyword", "Send caption keyword (default: 𝗥𝗮𝗿𝗶𝘁𝘆):"),
        "set_collection": ("📚", "collection_name", "Send MongoDB collection name:"),
        "set_target":     ("📢", "target_channel",  "Send target channel ID or @username:"),
        "set_keyboard":   ("⌨️", "keyboard_message","Send keyboard message text:"),
        "rm_waifu":       ("🗑", "rm_waifu_id",     "Send Waifu ID to delete from DB:"),
    }

    if action in prompts:
        emoji, field, prompt = prompts[action]
        _conv[user_id] = {"state": "await_simple", "field": field}
        await query.message.reply_text(
            f"{emoji} <b>{prompt}</b>\n\n<i>Send /cancel to abort.</i>",
            parse_mode=enums.ParseMode.HTML,
        )
        return await query.answer()

    # ── Remove fields ─────────────────────────────────────────────────────────

    removes = {
        "rm_session":    ("string_session",  "📱 String session removed!"),
        "rm_logger":     ("logger_channel",  "📋 Logger removed!"),
        "rm_collection": ("collection_name", "📚 Collection reset to default!"),
    }
    if action in removes:
        field, msg_text = removes[action]
        await unset_config(field)
        if action == "rm_session":
            await stop_userbot()
        await query.answer(msg_text, show_alert=True)
        return

    # ── Fetch all waifus ──────────────────────────────────────────────────────

    if action == "fetch_all":
        await query.answer("⏳ Starting bulk fetch…", show_alert=True)
        from WAIFUSCRPER.tools.dwonloder.Dwonlod import bulk_fetch
        asyncio.create_task(bulk_fetch(query.message))
        return

    # ── Listener toggle ───────────────────────────────────────────────────────

    if action == "toggle_listener":
        from WAIFUSCRPER.tools.dwonloder.Dwonlod import toggle_listener, _listener_active
        new_state = not _listener_active
        toggle_listener(new_state)
        await set_config(listener_enabled=new_state)
        await query.answer(
            f"📡 Listener {'🟢 ON' if new_state else '🔴 OFF'}",
            show_alert=True,
        )
        cfg   = await get_config()
        count = await waifu_count()
        await query.message.edit_text(
            f"⚙️ <b>Config — Page 3</b>\n\n"
            f"📢 Target   : <code>{cfg.get('target_channel', 'Not set')}</code>\n"
            f"🗂 Waifus   : <b>{count}</b> in DB\n"
            f"📡 Listener : <b>{'🟢 ON' if new_state else '🔴 OFF'}</b>",
            parse_mode=enums.ParseMode.HTML,
            reply_markup=_kb_page3(new_state),
        )
        return


# ── Text handler — handles all conversation flows ─────────────────────────────

@bot.on_message(filters.private & filters.text & ~filters.command(["start", "cancel", "addsudo", "rmsudo", "sudolist"]))
async def text_handler(client: Client, message: Message):
    user_id = message.from_user.id
    if not await _is_sudo(user_id):
        return

    conv = _conv.get(user_id)
    if not conv:
        return

    state = conv["state"]
    text  = message.text.strip()

    # ── Simple field set ──────────────────────────────────────────────────────
    if state == "await_simple":
        field = conv["field"]
        del _conv[user_id]

        if field == "rm_waifu_id":
            ok = await delete_waifu_by_id(text)
            if ok:
                await message.reply_text(f"✅ Waifu <code>{escape(text)}</code> deleted!", parse_mode=enums.ParseMode.HTML)
            else:
                await message.reply_text(f"❌ ID <code>{escape(text)}</code> not found.", parse_mode=enums.ParseMode.HTML)
            return

        await set_config(**{field: text})
        labels = {
            "logger_channel":  "📋 Logger channel",
            "approve_channel": "✅ Approve channel",
            "caption_keyword": "📝 Caption keyword",
            "collection_name": "📚 Collection name",
            "target_channel":  "📢 Target channel",
            "keyboard_message":"⌨️ Keyboard message",
        }
        await message.reply_text(
            f"✅ <b>{labels.get(field, field)}</b> → <code>{escape(text)}</code>",
            parse_mode=enums.ParseMode.HTML,
        )
        return

    # ── Session flow: phone ───────────────────────────────────────────────────
    if state == "await_phone":
        phone = text
        if not phone.startswith("+"):
            await message.reply_text(
                "❌ Phone must start with + (e.g. <code>+91XXXXXXXXXX</code>)\nSend again:",
                parse_mode=enums.ParseMode.HTML,
                reply_markup=_kb_cancel(),
            )
            return

        proc = await message.reply_text("⏳ Sending OTP…")

        # Create temp client
        temp_client = Client(
            name=f"session_gen_{user_id}",
            api_id=config.API_ID,
            api_hash=config.API_HASH,
            in_memory=True,
        )
        try:
            await temp_client.connect()
            sent = await temp_client.send_code(phone)
        except Exception as e:
            await proc.edit_text(f"❌ Failed to send OTP: {escape(str(e))}")
            await temp_client.disconnect()
            del _conv[user_id]
            return

        _gen_clients[user_id] = temp_client
        _otp_sessions[user_id] = {
            "phone":  phone,
            "hash":   sent.phone_code_hash,
        }
        _conv[user_id] = {"state": "await_otp", "attempts": 3}

        await proc.edit_text(
            f"📨 OTP sent to <code>{phone}</code>\n\n"
            f"Enter the OTP you received:\n"
            f"<i>(3 attempts remaining)</i>",
            parse_mode=enums.ParseMode.HTML,
            reply_markup=_kb_cancel(),
        )
        return

    # ── Session flow: OTP ─────────────────────────────────────────────────────
    if state == "await_otp":
        otp_data   = _otp_sessions.get(user_id, {})
        temp_client = _gen_clients.get(user_id)
        attempts   = conv.get("attempts", 3)

        if not temp_client or not otp_data:
            await message.reply_text("❌ Session expired. Start again via Config.")
            await _cleanup_flow(user_id)
            return

        try:
            await temp_client.sign_in(
                otp_data["phone"],
                otp_data["hash"],
                text,
            )
            # ── OTP success → export session ──────────────────────────────────
            await _finish_session(user_id, message, temp_client)
            return

        except PhoneCodeInvalid:
            attempts -= 1
            _conv[user_id]["attempts"] = attempts
            if attempts > 0:
                await message.reply_text(
                    f"❌ Wrong OTP! <b>{attempts}</b> attempt(s) left.\nTry again:",
                    parse_mode=enums.ParseMode.HTML,
                    reply_markup=_kb_cancel(),
                )
            else:
                await message.reply_text("❌ Too many wrong attempts. Start again via Config.")
                await _cleanup_flow(user_id)
            return

        except PhoneCodeExpired:
            await message.reply_text("❌ OTP expired! Click 📱 String Session again.")
            await _cleanup_flow(user_id)
            return

        except SessionPasswordNeeded:
            _conv[user_id] = {"state": "await_2fa"}
            await message.reply_text(
                "🔐 <b>Two-Factor Authentication</b>\n\n"
                "Your account has 2FA enabled.\n"
                "Send your 2FA password:",
                parse_mode=enums.ParseMode.HTML,
                reply_markup=_kb_cancel(),
            )
            return

    # ── Session flow: 2FA ─────────────────────────────────────────────────────
    if state == "await_2fa":
        temp_client = _gen_clients.get(user_id)
        if not temp_client:
            await message.reply_text("❌ Session expired. Start again.")
            await _cleanup_flow(user_id)
            return

        try:
            await temp_client.check_password(text)
            await _finish_session(user_id, message, temp_client)
        except BadRequest as e:
            await message.reply_text(
                f"❌ Wrong 2FA password: {escape(str(e))}\nTry again:",
                parse_mode=enums.ParseMode.HTML,
                reply_markup=_kb_cancel(),
            )
        return


# ── Finish session — export + save + start userbot ───────────────────────────

async def _finish_session(user_id: int, message: Message, temp_client: Client):
    try:
        session_string = await temp_client.export_session_string()
        me             = await temp_client.get_me()
    except Exception as e:
        await message.reply_text(f"❌ Failed to export session: {escape(str(e))}")
        await _cleanup_flow(user_id)
        return

    await temp_client.disconnect()

    proc = await message.reply_text(
        f"✅ <b>Logged in as {escape(me.first_name)} (<code>{me.id}</code>)</b>\n"
        f"⏳ Saving and starting userbot…",
        parse_mode=enums.ParseMode.HTML,
    )

    await set_config(string_session=session_string)

    ub = await start_userbot(session_string)
    if ub:
        cfg    = await get_config()
        target = cfg.get("target_channel")
        if target:
            from WAIFUSCRPER.tools.dwonloder.Dwonlod import setup_userbot_listener
            await setup_userbot_listener(ub, cfg)

        await proc.edit_text(
            f"<blockquote>🌸 <b>Userbot Started!</b></blockquote>\n\n"
            f"👤 Name  : <b>{escape(me.first_name)}</b>\n"
            f"🆔 ID    : <code>{me.id}</code>\n"
            f"📡 Monitoring: <code>{target or 'Not set'}</code>",
            parse_mode=enums.ParseMode.HTML,
        )
    else:
        await proc.edit_text("⚠️ Session saved but userbot failed to start. Check logs.")

    await _cleanup_flow(user_id)


# ── Flow timeout ──────────────────────────────────────────────────────────────

async def _flow_timeout(user_id: int, chat_id: int):
    await asyncio.sleep(INPUT_TIMEOUT)
    if user_id in _conv:
        await _cleanup_flow(user_id)
        try:
            await bot.send_message(
                chat_id,
                "⏰ <b>Session flow timed out.</b> Click 📱 String Session to try again.",
                parse_mode=enums.ParseMode.HTML,
            )
        except Exception:
            pass


# ── Cleanup ───────────────────────────────────────────────────────────────────

async def _cleanup_flow(user_id: int):
    _conv.pop(user_id, None)
    _otp_sessions.pop(user_id, None)
    client = _gen_clients.pop(user_id, None)
    if client:
        try:
            await client.disconnect()
        except Exception:
            pass


# ── Config status text ────────────────────────────────────────────────────────

async def _config_status(cfg: dict) -> str:
    count = await waifu_count()

    def val(k, default="❌ Not set"):
        v = cfg.get(k)
        return f"<code>{escape(str(v))}</code>" if v else f"<i>{default}</i>"

    sudos   = await get_sudos()
    session = "✅ Active" if cfg.get("string_session") else "❌ Not set"

    return (
        f"<blockquote>⚙️ <b>WaifuScrper Config</b></blockquote>\n\n"
        f"📋 Logger     : {val('logger_channel')}\n"
        f"✅ Approve    : {val('approve_channel')}\n"
        f"📱 Session    : <i>{session}</i>\n"
        f"📝 Keyword    : {val('caption_keyword', '𝗥𝗮𝗿𝗶𝘁𝘆 (default)')}\n"
        f"📢 Target     : {val('target_channel')}\n"
        f"📚 Collection : {val('collection_name', 'waifus (default)')}\n"
        f"🗂 In DB      : <b>{count}</b> waifus\n"
        f"🛡 Sudos      : <b>{len(sudos)}</b> users\n"
    )


# ── Help text ─────────────────────────────────────────────────────────────────

def _help_text() -> str:
    return (
        "<blockquote>❓ <b>WaifuScrper — Guide</b></blockquote>\n\n"
        "<b>Setup Steps:</b>\n"
        "1️⃣ Click <b>📱 String Session</b>\n"
        "   → Enter phone → OTP → 2FA (if any)\n"
        "2️⃣ Set <b>📢 Target Channel</b> to scrape from\n"
        "3️⃣ Set <b>📋 Logger Channel</b> for approvals\n"
        "4️⃣ Set <b>📚 Collection Name</b> (MongoDB)\n"
        "5️⃣ Set <b>📝 Caption Keyword</b>\n"
        "   (default: <code>𝗥𝗮𝗿𝗶𝘁𝘆</code>)\n\n"
        "<b>Commands:</b>\n"
        "<code>/addsudo 123456</code> — Add sudo user\n"
        "<code>/rmsudo 123456</code>  — Remove sudo user\n"
        "<code>/sudolist</code>       — List all sudos\n\n"
        "<b>Scraping:</b>\n"
        "• Config → 🔍 Fetch All → bulk fetch entire channel\n"
        "• Config → 🟢 Live Listener → auto-detect new posts\n"
        "• Each waifu → approval → ✅ saves to MongoDB\n\n"
        "<b>Caption format expected:</b>\n"
        "<code>Anime Name\n"
        "1234: Character Name\n"
        "𝗥𝗮𝗿𝗶𝘁𝘆: 🎐 Celestial</code>"
            )
