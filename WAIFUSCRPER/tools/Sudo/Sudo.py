from pyrogram import enums
"""
WAIFUSCRPER — Sudo.py
Commands:
  /addsudo  <user_id | reply>  — Add sudo user  (owner only)
  /rmsudo   <user_id | reply>  — Remove sudo user (owner only)
  /sudolist                    — List all sudo users
"""

from pyrogram import Client, filters
from pyrogram.types import Message
from loguru import logger

import config
from WAIFUSCRPER import app
from WAIFUSCRPER.Database import add_sudo, remove_sudo, get_sudo_users


# ── Owner-only filter ──────────────────────────────────────────────────────────

def _owner_only(_, __, msg: Message) -> bool:
    return msg.from_user and msg.from_user.id == config.OWNER_ID

owner_filter = filters.create(_owner_only)


# ── Helper: resolve user_id from command or reply ──────────────────────────────

def _resolve_user(message: Message) -> int | None:
    """
    Returns user_id from:
      1. /cmd <user_id>
      2. Reply to a message
    Returns None if neither found.
    """
    args = message.command[1:]
    if args:
        try:
            return int(args[0])
        except ValueError:
            return None

    if message.reply_to_message and message.reply_to_message.from_user:
        return message.reply_to_message.from_user.id

    return None


# ── /addsudo ───────────────────────────────────────────────────────────────────

@app.on_message(filters.command("addsudo") & owner_filter, group=0)
async def addsudo_handler(client: Client, message: Message):
    user_id = _resolve_user(message)

    if not user_id:
        return await message.reply_text(
            "❌ <b>ᴘʀᴏᴠɪᴅᴇ ᴀ ᴜsᴇʀ ɪᴅ ᴏʀ ʀᴇᴘʟʏ ᴛᴏ ᴀ ᴜsᴇʀ.</b>\n\n"
            "ᴜsᴀɢᴇ: <code>/addsudo 123456789</code>",
            parse_mode=enums.ParseMode.HTML,
        )

    if user_id == config.OWNER_ID:
        return await message.reply_text(
            "👑 <b>ᴏᴡɴᴇʀ ɪs ᴀʟʀᴇᴀᴅʏ ᴀᴛ ᴛʜᴇ ᴛᴏᴘ!</b>",
            parse_mode=enums.ParseMode.HTML,
        )

    existing = await get_sudo_users()
    if user_id in existing:
        return await message.reply_text(
            f"⚠️ <code>{user_id}</code> <b>ɪs ᴀʟʀᴇᴀᴅʏ ᴀ sᴜᴅᴏ ᴜsᴇʀ.</b>",
            parse_mode=enums.ParseMode.HTML,
        )

    await add_sudo(user_id)
    logger.info(f"Sudo added: {user_id} by owner")

    await message.reply_text(
        f"✅ <code>{user_id}</code> <b>ʜᴀs ʙᴇᴇɴ ɢʀᴀɴᴛᴇᴅ sᴜᴅᴏ ᴀᴄᴄᴇss!</b>",
        parse_mode=enums.ParseMode.HTML,
    )


# ── /rmsudo ────────────────────────────────────────────────────────────────────

@app.on_message(filters.command("rmsudo") & owner_filter, group=0)
async def rmsudo_handler(client: Client, message: Message):
    user_id = _resolve_user(message)

    if not user_id:
        return await message.reply_text(
            "❌ <b>ᴘʀᴏᴠɪᴅᴇ ᴀ ᴜsᴇʀ ɪᴅ ᴏʀ ʀᴇᴘʟʏ ᴛᴏ ᴀ ᴜsᴇʀ.</b>\n\n"
            "ᴜsᴀɢᴇ: <code>/rmsudo 123456789</code>",
            parse_mode=enums.ParseMode.HTML,
        )

    if user_id == config.OWNER_ID:
        return await message.reply_text(
            "😂 <b>ᴄᴀɴɴᴏᴛ ʀᴇᴍᴏᴠᴇ ᴛʜᴇ ᴏᴡɴᴇʀ!</b>",
            parse_mode=enums.ParseMode.HTML,
        )

    existing = await get_sudo_users()
    if user_id not in existing:
        return await message.reply_text(
            f"⚠️ <code>{user_id}</code> <b>ɪs ɴᴏᴛ ɪɴ ᴛʜᴇ sᴜᴅᴏ ʟɪsᴛ.</b>",
            parse_mode=enums.ParseMode.HTML,
        )

    await remove_sudo(user_id)
    logger.info(f"Sudo removed: {user_id} by owner")

    await message.reply_text(
        f"✅ <code>{user_id}</code> <b>ʜᴀs ʙᴇᴇɴ ʀᴇᴍᴏᴠᴇᴅ ꜰʀᴏᴍ sᴜᴅᴏ!</b>",
        parse_mode=enums.ParseMode.HTML,
    )


# ── /sudolist ──────────────────────────────────────────────────────────────────

@app.on_message(filters.command("sudolist") & owner_filter, group=0)
async def sudolist_handler(client: Client, message: Message):
    sudo_users = await get_sudo_users()

    if not sudo_users:
        return await message.reply_text(
            "📭 <b>ɴᴏ sᴜᴅᴏ ᴜsᴇʀs ꜰᴏᴜɴᴅ.</b>",
            parse_mode=enums.ParseMode.HTML,
        )

    lines = [
        f"👑 <b>ᴏᴡɴᴇʀ :</b> <code>{config.OWNER_ID}</code>\n",
        f"🛡 <b>sᴜᴅᴏ ᴜsᴇʀs ({len(sudo_users)}) :</b>",
    ]

    for uid in sudo_users:
        try:
            user     = await client.get_users(uid)
            name     = user.first_name
            username = f"@{user.username}" if user.username else "ɴᴏ ᴜsᴇʀɴᴀᴍᴇ"
            lines.append(
                f"  • <a href='tg://user?id={uid}'>{name}</a> "
                f"({username}) — <code>{uid}</code>"
            )
        except Exception:
            lines.append(f"  • <code>{uid}</code>")

    await message.reply_text(
        "\n".join(lines),
        parse_mode=enums.ParseMode.HTML,
        disable_web_page_preview=True,
    )

  
