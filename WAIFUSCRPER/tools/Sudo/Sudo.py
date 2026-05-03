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

@Client.on_message(filters.command("addsudo") & owner_filter)
async def addsudo_handler(client: Client, message: Message):
    """
    Add a sudo user.
    Usage:
      /addsudo <user_id>
      Reply to a message + /addsudo
    """
    user_id = _resolve_user(message)

    if not user_id:
        return await message.reply_text(
            "❌ Provide a user ID or reply to a user.\n"
            "Usage: <code>/addsudo 123456789</code>",
            parse_mode="html",
        )

    if user_id == config.OWNER_ID:
        return await message.reply_text("👑 Owner toh already top pe hai bhai!")

    existing = await get_sudo_users()
    if user_id in existing:
        return await message.reply_text(
            f"⚠️ <code>{user_id}</code> already sudo hai.",
            parse_mode="html",
        )

    await add_sudo(user_id)
    logger.info(f"Sudo added: {user_id} by owner")

    await message.reply_text(
        f"✅ <code>{user_id}</code> ko sudo diya gaya!",
        parse_mode="html",
    )


# ── /rmsudo ────────────────────────────────────────────────────────────────────

@Client.on_message(filters.command("rmsudo") & owner_filter)
async def rmsudo_handler(client: Client, message: Message):
    """
    Remove a sudo user.
    Usage:
      /rmsudo <user_id>
      Reply to a message + /rmsudo
    """
    user_id = _resolve_user(message)

    if not user_id:
        return await message.reply_text(
            "❌ Provide a user ID or reply to a user.\n"
            "Usage: <code>/rmsudo 123456789</code>",
            parse_mode="html",
        )

    if user_id == config.OWNER_ID:
        return await message.reply_text("😂 Owner ko remove nahi kar sakta bhai!")

    existing = await get_sudo_users()
    if user_id not in existing:
        return await message.reply_text(
            f"⚠️ <code>{user_id}</code> sudo list mein hai hi nahi.",
            parse_mode="html",
        )

    await remove_sudo(user_id)
    logger.info(f"Sudo removed: {user_id} by owner")

    await message.reply_text(
        f"✅ <code>{user_id}</code> ko sudo se hata diya!",
        parse_mode="html",
    )


# ── /sudolist ──────────────────────────────────────────────────────────────────

@Client.on_message(filters.command("sudolist") & owner_filter)
async def sudolist_handler(client: Client, message: Message):
    """List all current sudo users."""
    sudo_users = await get_sudo_users()

    if not sudo_users:
        return await message.reply_text("📭 Koi sudo user nahi hai abhi.")

    lines = [f"👑 <b>Owner:</b> <code>{config.OWNER_ID}</code>\n"]
    lines.append(f"🛡 <b>Sudo Users ({len(sudo_users)}):</b>")

    for uid in sudo_users:
        try:
            user = await client.get_users(uid)
            name = user.first_name
            username = f"@{user.username}" if user.username else "no username"
            lines.append(f"  • <a href='tg://user?id={uid}'>{name}</a> ({username}) — <code>{uid}</code>")
        except Exception:
            lines.append(f"  • <code>{uid}</code>")

    await message.reply_text(
        "\n".join(lines),
        parse_mode="html",
        disable_web_page_preview=True,
    )
    
