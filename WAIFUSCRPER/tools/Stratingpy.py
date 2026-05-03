import asyncio

from pyrogram import Client, filters, enums
from pyrogram.handlers import MessageHandler
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

INPUT_TIMEOUT = 120

_active: dict[int, bool] = {}


def _is_authorized(user_id: int) -> bool:
    return user_id == config.OWNER_ID or user_id in config.SUDO_USERS


async def _wait_for_reply(client: Client, user_id: int, timeout: int = INPUT_TIMEOUT) -> str | None:
    """
    wait for user's next private text message.
    returns message text or none on timeout / cancel.
    """
    future: asyncio.Future = asyncio.get_event_loop().create_future()

    async def _cb(c: Client, m: Message):
        if not future.done():
            future.set_result(m.text.strip())
        try:
            await m.delete()
        except Exception:
            pass

    handler = MessageHandler(
        _cb,
        filters.private & filters.text & filters.user(user_id),
    )
    client.add_handler(handler, group=99)

    try:
        return await asyncio.wait_for(future, timeout=timeout)
    except asyncio.TimeoutError:
        return None
    finally:
        client.remove_handler(handler, group=99)


@app.on_message(filters.command("cancel") & filters.private)
async def cmd_cancel(client: Client, message: Message):
    uid = message.from_user.id
    if uid in _active:
        _active.pop(uid)
        await message.reply_text(
            "❌ <b>session setup cancelled.</b>",
            parse_mode=enums.ParseMode.HTML,
        )
    else:
        await message.reply_text(
            "⚠️ <b>no active setup running.</b>",
            parse_mode=enums.ParseMode.HTML,
        )


@app.on_message(filters.command("setsession") & filters.private)
async def cmd_setsession(client: Client, message: Message):
    uid = message.from_user.id

    if not _is_authorized(uid):
        return await message.reply_text("🚫 permission denied!", parse_mode=enums.ParseMode.HTML)

    if uid in _active:
        return await message.reply_text(
            "⚠️ a session setup is already running.\nuse /cancel to stop it first.",
            parse_mode=enums.ParseMode.HTML,
        )

    _active[uid] = True

    step1 = await message.reply_text(
        "🔐 <b>string session setup</b>\n\n"
        "<b>step 1/3</b> — send your phone number:\n"
        "<i>(format: +91xxxxxxxxxx)</i>\n\n"
        "<i>use /cancel to abort.</i>",
        parse_mode=enums.ParseMode.HTML,
    )

    phone = await _wait_for_reply(client, uid)
    if not phone or uid not in _active:
        _active.pop(uid, None)
        return await step1.edit_text(
            "⏰ <b>timeout or cancelled.</b>  setup stopped.",
            parse_mode=enums.ParseMode.HTML,
        )

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
            f"❌ <b>connection failed:</b> <code>{e}</code>",
            parse_mode=enums.ParseMode.HTML,
        )

    try:
        sent_code = await temp.send_code(phone)
    except PhoneNumberInvalid:
        _active.pop(uid, None)
        await temp.disconnect()
        return await step1.edit_text(
            "❌ <b>invalid phone number!</b>  check and try again.",
            parse_mode=enums.ParseMode.HTML,
        )
    except FloodWait as e:
        _active.pop(uid, None)
        await temp.disconnect()
        return await step1.edit_text(
            f"⏳ <b>floodwait:</b>  try again after {e.value}s.",
            parse_mode=enums.ParseMode.HTML,
        )
    except Exception as e:
        _active.pop(uid, None)
        await temp.disconnect()
        return await step1.edit_text(
            f"❌ <b>error:</b> <code>{e}</code>",
            parse_mode=enums.ParseMode.HTML,
        )

    step2 = await step1.edit_text(
        "🔐 <b>string session setup</b>\n\n"
        "<b>step 2/3</b> — send the otp:\n"
        "<i>(the code telegram sent you — spaces are fine)</i>\n\n"
        "<i>use /cancel to abort.</i>",
        parse_mode=enums.ParseMode.HTML,
    )

    otp_raw = await _wait_for_reply(client, uid)
    if not otp_raw or uid not in _active:
        _active.pop(uid, None)
        await temp.disconnect()
        return await step2.edit_text(
            "⏰ <b>timeout or cancelled.</b>  setup stopped.",
            parse_mode=enums.ParseMode.HTML,
        )

    otp = otp_raw.replace(" ", "").replace("-", "")

    try:
        await temp.sign_in(phone, sent_code.phone_code_hash, otp)

    except SessionPasswordNeeded:
        step3 = await step2.edit_text(
            "🔐 <b>string session setup</b>\n\n"
            "<b>step 3/3</b> — send your 2fa password:\n"
            "<i>(your telegram cloud password)</i>\n\n"
            "<i>use /cancel to abort.</i>",
            parse_mode=enums.ParseMode.HTML,
        )

        password = await _wait_for_reply(client, uid)
        if not password or uid not in _active:
            _active.pop(uid, None)
            await temp.disconnect()
            return await step3.edit_text(
                "⏰ <b>timeout or cancelled.</b>  setup stopped.",
                parse_mode=enums.ParseMode.HTML,
            )

        try:
            await temp.check_password(password)
        except PasswordHashInvalid:
            _active.pop(uid, None)
            await temp.disconnect()
            return await step3.edit_text(
                "❌ <b>wrong 2fa password!</b>  try /setsession again.",
                parse_mode=enums.ParseMode.HTML,
            )
        except Exception as e:
            _active.pop(uid, None)
            await temp.disconnect()
            return await step3.edit_text(
                f"❌ <b>2fa error:</b> <code>{e}</code>",
                parse_mode=enums.ParseMode.HTML,
            )

        await step3.edit_text("✅ <b>2fa verified!</b>  saving session...", parse_mode=enums.ParseMode.HTML)

    except PhoneCodeInvalid:
        _active.pop(uid, None)
        await temp.disconnect()
        return await step2.edit_text(
            "❌ <b>wrong otp!</b>  try /setsession again.",
            parse_mode=enums.ParseMode.HTML,
        )
    except PhoneCodeExpired:
        _active.pop(uid, None)
        await temp.disconnect()
        return await step2.edit_text(
            "❌ <b>otp expired!</b>  try /setsession again.",
            parse_mode=enums.ParseMode.HTML,
        )
    except Exception as e:
        _active.pop(uid, None)
        await temp.disconnect()
        return await step2.edit_text(
            f"❌ <b>sign-in error:</b> <code>{e}</code>",
            parse_mode=enums.ParseMode.HTML,
        )

    try:
        session_string = await temp.export_session_string()
        await set_string_session(session_string)
        log.success(f"string session saved for user {uid}")

        await temp.disconnect()
        _active.pop(uid, None)

        await message.reply_text(
            "✅ <b>string session saved!</b>\n\n"
            "you can now start scraping with /wstart.\n\n"
            "<i>session is stored in db — no need to login again.</i>",
            parse_mode=enums.ParseMode.HTML,
        )

    except Exception as e:
        _active.pop(uid, None)
        try:
            await temp.disconnect()
        except Exception:
            pass
        await message.reply_text(
            f"❌ <b>session export error:</b> <code>{e}</code>",
            parse_mode=enums.ParseMode.HTML,
      )
      
