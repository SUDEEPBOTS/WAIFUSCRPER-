"""
WAIFUSCRPER — tools/Stratingpy.py
String Session setup via bot:
  /setsession  →  Phone → OTP → 2FA (if enabled) → Save to DB

Timeout: 120 seconds per step.
/cancel to abort at any step.
"""

import asyncio

from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.errors import (
    PhoneNumberInvalid,
    PhoneCodeInvalid,
    PhoneCodeExpired,
    SessionPasswordNeeded,
    PasswordHashInvalid,
    FloodWait,
)

import config
from WAIFUSCRPER import app
from WAIFUSCRPER.Logging import LOGGER
from WAIFUSCRPER.Database import set_string_session

log = LOGGER(__name__)

INPUT_TIMEOUT = 120   # seconds per step

# Active sessions  { user_id: asyncio.Event }
_active: dict[int, bool] = {}


def _is_authorized(user_id: int) -> bool:
    return user_id == config.OWNER_ID or user_id in config.SUDO_USERS


async def _wait_for_reply(client: Client, user_id: int, timeout: int = INPUT_TIMEOUT) -> str | None:
    """
    Wait for user's next private text message.
    Returns message text or None on timeout / cancel.
    """
    future: asyncio.Future = asyncio.get_event_loop().create_future()

    @client.on_message(filters.private & filters.text & filters.user(user_id))
    async def _handler(c: Client, m: Message):
        if not future.done():
            future.set_result(m.text.strip())
        await m.delete()   # Clean up input message

    try:
        return await asyncio.wait_for(future, timeout=timeout)
    except asyncio.TimeoutError:
        return None
    finally:
        client.remove_handler(_handler)


# ══════════════════════════════════════════════════════════════════════════════
#  /cancel COMMAND  — abort any running session setup
# ══════════════════════════════════════════════════════════════════════════════

@app.on_message(filters.command("cancel") & filters.private)
async def cmd_cancel(client: Client, message: Message):
    uid = message.from_user.id
    if uid in _active:
        _active.pop(uid)
        await message.reply_text(
            "❌ <b>Session setup cancel kar diya.</b>",
            parse_mode="html",
        )
    else:
        await message.reply_text(
            "⚠️ <b>Koi active setup nahi chal raha.</b>",
            parse_mode="html",
        )


# ══════════════════════════════════════════════════════════════════════════════
#  /setsession COMMAND
# ══════════════════════════════════════════════════════════════════════════════

@app.on_message(filters.command("setsession") & filters.private)
async def cmd_setsession(client: Client, message: Message):
    uid = message.from_user.id

    if not _is_authorized(uid):
        return await message.reply_text("🚫 Permission nahi hai!", parse_mode="html")

    if uid in _active:
        return await message.reply_text(
            "⚠️ Ek session setup pehle se chal raha hai.\n"
            "/cancel se band karo pehle.",
            parse_mode="html",
        )

    _active[uid] = True

    # ── Step 1: Phone number ───────────────────────────────────────────────────
    step1 = await message.reply_text(
        "🔐 <b>String Session Setup</b>\n\n"
        "<b>Step 1/3</b> — Phone number bhejo:\n"
        "<i>(Format: +91XXXXXXXXXX)</i>\n\n"
        "<i>/cancel se band karo.</i>",
        parse_mode="html",
    )

    phone = await _wait_for_reply(client, uid)
    if not phone or uid not in _active:
        _active.pop(uid, None)
        return await step1.edit_text(
            "⏰ <b>Timeout ya cancel!</b>  Setup band ho gaya.",
            parse_mode="html",
        )

    # Create a temporary Pyrogram client for login
    temp = Client(
        name=f"temp_session_{uid}",
        api_id=config.API_ID,
        api_hash=config.API_HASH,
        in_memory=True,
    )

    try:
        await temp.connect()
    except Exception as e:
        _active.pop(uid, None)
        return await step1.edit_text(
            f"❌ <b>Connection failed:</b> <code>{e}</code>",
            parse_mode="html",
        )

    # Send OTP
    try:
        sent_code = await temp.send_code(phone)
    except PhoneNumberInvalid:
        _active.pop(uid, None)
        await temp.disconnect()
        return await step1.edit_text(
            "❌ <b>Invalid phone number!</b>  Check karke dobara try karo.",
            parse_mode="html",
        )
    except FloodWait as e:
        _active.pop(uid, None)
        await temp.disconnect()
        return await step1.edit_text(
            f"⏳ <b>FloodWait:</b>  {e.value}s baad try karo.",
            parse_mode="html",
        )
    except Exception as e:
        _active.pop(uid, None)
        await temp.disconnect()
        return await step1.edit_text(
            f"❌ <b>Error:</b> <code>{e}</code>",
            parse_mode="html",
        )

    # ── Step 2: OTP ────────────────────────────────────────────────────────────
    step2 = await step1.edit_text(
        "🔐 <b>String Session Setup</b>\n\n"
        "<b>Step 2/3</b> — OTP bhejo:\n"
        "<i>(Telegram ne jo code bheja — spaces ke saath bhi chalega)</i>\n\n"
        "<i>/cancel se band karo.</i>",
        parse_mode="html",
    )

    otp_raw = await _wait_for_reply(client, uid)
    if not otp_raw or uid not in _active:
        _active.pop(uid, None)
        await temp.disconnect()
        return await step2.edit_text(
            "⏰ <b>Timeout ya cancel!</b>  Setup band ho gaya.",
            parse_mode="html",
        )

    otp = otp_raw.replace(" ", "").replace("-", "")

    try:
        await temp.sign_in(phone, sent_code.phone_code_hash, otp)

    except SessionPasswordNeeded:
        # ── Step 3: 2FA ────────────────────────────────────────────────────────
        step3 = await step2.edit_text(
            "🔐 <b>String Session Setup</b>\n\n"
            "<b>Step 3/3</b> — 2FA Password bhejo:\n"
            "<i>(Telegram account ka cloud password)</i>\n\n"
            "<i>/cancel se band karo.</i>",
            parse_mode="html",
        )

        password = await _wait_for_reply(client, uid)
        if not password or uid not in _active:
            _active.pop(uid, None)
            await temp.disconnect()
            return await step3.edit_text(
                "⏰ <b>Timeout ya cancel!</b>  Setup band ho gaya.",
                parse_mode="html",
            )

        try:
            await temp.check_password(password)
        except PasswordHashInvalid:
            _active.pop(uid, None)
            await temp.disconnect()
            return await step3.edit_text(
                "❌ <b>Wrong 2FA password!</b>  Dobara /setsession se try karo.",
                parse_mode="html",
            )
        except Exception as e:
            _active.pop(uid, None)
            await temp.disconnect()
            return await step3.edit_text(
                f"❌ <b>2FA Error:</b> <code>{e}</code>",
                parse_mode="html",
            )

        await step3.edit_text("✅ <b>2FA verified!</b>  Session save ho raha hai...", parse_mode="html")

    except PhoneCodeInvalid:
        _active.pop(uid, None)
        await temp.disconnect()
        return await step2.edit_text(
            "❌ <b>Wrong OTP!</b>  Dobara /setsession se try karo.",
            parse_mode="html",
        )
    except PhoneCodeExpired:
        _active.pop(uid, None)
        await temp.disconnect()
        return await step2.edit_text(
            "❌ <b>OTP expired!</b>  Dobara /setsession se try karo.",
            parse_mode="html",
        )
    except Exception as e:
        _active.pop(uid, None)
        await temp.disconnect()
        return await step2.edit_text(
            f"❌ <b>Sign-in Error:</b> <code>{e}</code>",
            parse_mode="html",
        )

    # ── Export & Save ───────────────────────────────────────────────────────────
    try:
        session_string = await temp.export_session_string()
        await set_string_session(session_string)
        log.success(f"String session saved for user {uid}")

        await temp.disconnect()
        _active.pop(uid, None)

        await message.reply_text(
            "✅ <b>String Session save ho gayi!</b>\n\n"
            "Ab /wstart se scraping shuru kar sakte ho.\n\n"
            "<i>Session DB mein hai — dobara login ki zarurat nahi.</i>",
            parse_mode="html",
        )

    except Exception as e:
        _active.pop(uid, None)
        try:
            await temp.disconnect()
        except Exception:
            pass
        await message.reply_text(
            f"❌ <b>Session export error:</b> <code>{e}</code>",
            parse_mode="html",
        )

