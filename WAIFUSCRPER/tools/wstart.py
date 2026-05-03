"""
WAIFUSCRPER — tools/Wstart.py

/wstart flow:
  1. Userbot connect karo (string session DB se)
  2. Target channel mein photos count karo
  3. Confirm karo
  4. Approve mode ON  → har waifu logger pe bhejo, approve/skip wait karo
     Approve mode OFF → auto process
  5. Download → Upload → DB Save
  6. Progress updates
"""

import asyncio

from pyrogram import Client, filters
from pyrogram.errors import (
    ChannelInvalid,
    ChannelPrivate,
    UsernameNotOccupied,
    FloodWait,
)
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
    get_string_session,
    get_target_channel,
    get_approve_mode,
    get_logger,
)
from WAIFUSCRPER.tools.dwonloder.Dwonlod import process_waifu_message

log = LOGGER(__name__)

# ══════════════════════════════════════════════════════════════════════════════
#  STATE
# ══════════════════════════════════════════════════════════════════════════════

# Active scrape sessions  { user_id: {"task": Task, "running": bool} }
_scrape_sessions: dict[int, dict] = {}

# Pending approvals  { approve_key: asyncio.Event }
# approve_key = f"{logger_msg_id}"
_pending: dict[str, asyncio.Event] = {}
_results: dict[str, bool] = {}          # True = approved, False = skipped

PROGRESS_EVERY = 10    # Har 10 waifus ke baad update bhejo


# ══════════════════════════════════════════════════════════════════════════════
#  HELPERS
# ══════════════════════════════════════════════════════════════════════════════

def _is_authorized(user_id: int) -> bool:
    return user_id == config.OWNER_ID or user_id in config.SUDO_USERS


async def _get_userbot() -> Client | None:
    """
    String session se ek Pyrogram userbot client banao aur connect karo.
    Returns connected Client, ya None if session nahi hai.
    """
    session_string = await get_string_session()
    if not session_string:
        return None

    userbot = Client(
        name="userbot_scraper",
        api_id=config.API_ID,
        api_hash=config.API_HASH,
        session_string=session_string,
        no_updates=True,        # Sirf reading ke liye — updates band
    )
    await userbot.start()
    return userbot


async def _count_photos(userbot: Client, channel) -> int:
    """Channel mein sirf photo wale messages count karo."""
    count = 0
    async for msg in userbot.get_chat_history(channel):
        if msg.photo:
            count += 1
    return count


def _approve_keyboard(key: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Approve",  callback_data=f"wapprove_{key}"),
            InlineKeyboardButton("❌ Skip",     callback_data=f"wskip_{key}"),
        ]
    ])


async def _ask_approve(logger_id: int, userbot_msg, parsed: dict) -> bool:
    """
    Logger group pe waifu bhejo, approve/skip wait karo.
    Returns True = approved, False = skipped.
    Timeout: 5 minutes (300 seconds).
    """
    caption = (
        f"🆕 <b>Naya Waifu — Approve karo?</b>\n\n"
        f"📛 <b>Name:</b>  {parsed.get('name', 'Unknown')}\n"
        f"🎭 <b>Series:</b>  {parsed.get('series', 'Unknown')}\n"
        f"⭐ <b>Rarity:</b>  {parsed.get('rarity', 'Unknown')}\n"
        f"🆔 <b>ID:</b>  {parsed.get('waifu_id', 'Auto')}\n"
        f"👤 <b>Added by:</b>  {parsed.get('added_by', 'Unknown')}\n"
    )

    # Logger pe photo bhejo
    sent = await app.send_photo(
        chat_id=logger_id,
        photo=userbot_msg.photo.file_id,
        caption=caption,
        reply_markup=_approve_keyboard(str(sent_id := 0)),   # placeholder
        parse_mode="html",
    )
    # Ab actual message ID se key banao
    key = str(sent.id)

    # Keyboard dobara set karo sahi key ke saath
    await sent.edit_reply_markup(_approve_keyboard(key))

    # Event banao aur wait karo
    event = asyncio.Event()
    _pending[key] = event

    try:
        await asyncio.wait_for(event.wait(), timeout=300)
        return _results.pop(key, False)
    except asyncio.TimeoutError:
        log.warning(f"Approve timeout — key={key} ({parsed.get('name')})")
        _pending.pop(key, None)
        _results.pop(key, None)
        try:
            await sent.edit_caption(
                caption + "\n\n⏰ <i>Timeout — skipped.</i>",
                parse_mode="html",
            )
            await sent.edit_reply_markup(None)
        except Exception:
            pass
        return False


# ══════════════════════════════════════════════════════════════════════════════
#  APPROVE / SKIP CALLBACKS
# ══════════════════════════════════════════════════════════════════════════════

@app.on_callback_query(filters.regex(r"^w(approve|skip)_(\d+)$"))
async def cb_approve_skip(client: Client, cq: CallbackQuery):
    if not _is_authorized(cq.from_user.id):
        return await cq.answer("🚫 Permission nahi hai!", show_alert=True)

    action = cq.matches[0].group(1)   # "approve" or "skip"
    key    = cq.matches[0].group(2)

    if key not in _pending:
        return await cq.answer("⚠️ Yeh request expired ho gayi.", show_alert=True)

    approved = action == "approve"
    _results[key] = approved
    _pending[key].set()

    label = "✅ Approved" if approved else "❌ Skipped"
    await cq.answer(label)

    try:
        original_caption = cq.message.caption or ""
        await cq.message.edit_caption(
            original_caption + f"\n\n<b>{label} by {cq.from_user.first_name}</b>",
            parse_mode="html",
        )
        await cq.message.edit_reply_markup(None)
    except Exception:
        pass


# ══════════════════════════════════════════════════════════════════════════════
#  MAIN SCRAPE LOOP
# ══════════════════════════════════════════════════════════════════════════════

async def _scrape_loop(
    userbot: Client,
    channel,
    approve_mode: bool,
    logger_id: int | None,
    status_msg: Message,
    user_id: int,
) -> None:
    """
    Poora channel scan karo aur waifus process karo.
    Progress har PROGRESS_EVERY waifus pe update hoti hai.
    """
    total     = 0
    saved     = 0
    skipped   = 0
    errors    = 0
    processed = 0

    try:
        async for msg in userbot.get_chat_history(channel):

            # User ne stop kiya?
            session = _scrape_sessions.get(user_id, {})
            if not session.get("running", True):
                log.info(f"Scrape stopped by user {user_id}")
                break

            if not msg.photo:
                continue

            total += 1

            try:
                if approve_mode and logger_id:
                    # ── Parse karo pehle ──────────────────────────────────────
                    from WAIFUSCRPER.tools.dwonloder.Dwonlod import parse_caption
                    parsed = parse_caption(msg.caption or "")

                    if not parsed:
                        skipped += 1
                        continue

                    # ── Approve manga ─────────────────────────────────────────
                    approved = await _ask_approve(logger_id, msg, parsed)
                    if not approved:
                        skipped += 1
                        continue

                # ── Process (download → upload → save) ────────────────────────
                result = await process_waifu_message(userbot, msg)

                if result:
                    saved += 1
                    log.success(
                        f"[{saved}] Saved → {result.get('name')} "
                        f"| {result.get('rarity')}"
                    )
                else:
                    skipped += 1

            except FloodWait as e:
                log.warning(f"FloodWait {e.value}s — waiting...")
                await asyncio.sleep(e.value)
            except Exception as e:
                log.error(f"Error on msg {msg.id}: {e}")
                errors += 1

            processed += 1

            # ── Progress update ────────────────────────────────────────────────
            if processed % PROGRESS_EVERY == 0:
                try:
                    await status_msg.edit_text(
                        f"⏳ <b>Scraping chal raha hai...</b>\n\n"
                        f"📊 <b>Processed:</b>  {processed}\n"
                        f"✅ <b>Saved:</b>      {saved}\n"
                        f"⏭ <b>Skipped:</b>    {skipped}\n"
                        f"❌ <b>Errors:</b>     {errors}\n\n"
                        f"<i>/wstop se band karo.</i>",
                        parse_mode="html",
                    )
                except Exception:
                    pass

    except Exception as e:
        log.error(f"Scrape loop crashed: {e}")

    finally:
        # ── Stop userbot ───────────────────────────────────────────────────────
        try:
            await userbot.stop()
        except Exception:
            pass

        # ── Final report ───────────────────────────────────────────────────────
        _scrape_sessions.pop(user_id, None)

        try:
            await status_msg.edit_text(
                f"🎉 <b>Scraping Complete!</b>\n\n"
                f"📊 <b>Total scanned:</b>  {processed}\n"
                f"✅ <b>Saved:</b>          {saved}\n"
                f"⏭ <b>Skipped:</b>        {skipped}\n"
                f"❌ <b>Errors:</b>         {errors}\n\n"
                f"<i>MongoDB mein {saved} naye waifus add hue.</i>",
                parse_mode="html",
            )
        except Exception:
            pass

        log.info(
            f"Scrape done — {saved} saved / {skipped} skipped / "
            f"{errors} errors  (user={user_id})"
        )


# ══════════════════════════════════════════════════════════════════════════════
#  /wstart COMMAND
# ══════════════════════════════════════════════════════════════════════════════

@app.on_message(filters.command("wstart") & filters.private)
async def cmd_wstart(client: Client, message: Message):
    user_id = message.from_user.id

    if not _is_authorized(user_id):
        return await message.reply_text(
            "🚫 <b>Sirf owner ya sudo user use kar sakta hai.</b>",
            parse_mode="html",
        )

    # Already running?
    if user_id in _scrape_sessions:
        return await message.reply_text(
            "⚠️ <b>Ek scrape session pehle se chal raha hai!</b>\n"
            "/wstop se band karo pehle.",
            parse_mode="html",
        )

    # ── Config check ──────────────────────────────────────────────────────────
    wait = await message.reply_text("🔍 Config check kar raha hoon...", parse_mode="html")

    target_channel = await get_target_channel()
    if not target_channel:
        return await wait.edit_text(
            "❌ <b>Target Channel set nahi hai!</b>\n"
            "Config → Set Target Channel mein set karo.",
            parse_mode="html",
        )

    string_session = await get_string_session()
    if not string_session:
        return await wait.edit_text(
            "❌ <b>String Session set nahi hai!</b>\n"
            "/setsession se pehle login karo.",
            parse_mode="html",
        )

    approve_mode = await get_approve_mode()
    logger_id    = await get_logger() if approve_mode else None

    if approve_mode and not logger_id:
        return await wait.edit_text(
            "❌ <b>Approve Mode ON hai par Logger set nahi!</b>\n"
            "Config → Set Logger mein Logger group ID dalo.",
            parse_mode="html",
        )

    # ── Userbot connect ───────────────────────────────────────────────────────
    await wait.edit_text("🔌 Userbot connect ho raha hai...", parse_mode="html")

    userbot = await _get_userbot()
    if not userbot:
        return await wait.edit_text(
            "❌ <b>Userbot connect nahi hua.</b>\n"
            "String session check karo.",
            parse_mode="html",
        )

    # ── Channel join check + count ────────────────────────────────────────────
    await wait.edit_text(
        "📡 Channel check kar raha hoon aur waifus count kar raha hoon...\n"
        "<i>(Bade channel pe time lag sakta hai)</i>",
        parse_mode="html",
    )

    try:
        chat = await userbot.get_chat(target_channel)
    except (ChannelInvalid, ChannelPrivate, UsernameNotOccupied) as e:
        await userbot.stop()
        return await wait.edit_text(
            f"❌ <b>Channel access nahi mila:</b> <code>{e}</code>\n\n"
            "Check karo:\n"
            "• Channel ID sahi hai?\n"
            "• Userbot us channel mein hai?",
            parse_mode="html",
        )
    except Exception as e:
        await userbot.stop()
        return await wait.edit_text(
            f"❌ <b>Error:</b> <code>{e}</code>",
            parse_mode="html",
        )

    # Count photos
    try:
        photo_count = await _count_photos(userbot, target_channel)
    except Exception as e:
        await userbot.stop()
        return await wait.edit_text(
            f"❌ <b>Count error:</b> <code>{e}</code>",
            parse_mode="html",
        )

    # ── Confirm message ───────────────────────────────────────────────────────
    await wait.edit_text(
        f"📋 <b>Channel Info</b>\n\n"
        f"📣 <b>Channel:</b>  {chat.title}\n"
        f"🖼 <b>Waifu photos:</b>  <code>{photo_count}</code>\n"
        f"✅ <b>Approve Mode:</b>  {'ON 🟢' if approve_mode else 'OFF 🔴'}\n\n"
        f"<b>Scraping shuru karein?</b>",
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    "✅ Haan, Shuru Karo!",
                    callback_data=f"wstart_confirm_{user_id}",
                ),
                InlineKeyboardButton(
                    "❌ Nahi",
                    callback_data=f"wstart_cancel_{user_id}",
                ),
            ]
        ]),
        parse_mode="html",
    )

    # Userbot ko state mein rakh — confirm pe use karenge
    _scrape_sessions[user_id] = {
        "running":      False,
        "userbot":      userbot,
        "channel":      target_channel,
        "approve_mode": approve_mode,
        "logger_id":    logger_id,
        "status_msg":   wait,
        "task":         None,
    }


# ══════════════════════════════════════════════════════════════════════════════
#  CONFIRM / CANCEL CALLBACKS
# ══════════════════════════════════════════════════════════════════════════════

@app.on_callback_query(filters.regex(r"^wstart_confirm_(\d+)$"))
async def cb_wstart_confirm(client: Client, cq: CallbackQuery):
    owner_id = int(cq.matches[0].group(1))

    # Sirf wahi user confirm kare jisne /wstart kiya
    if cq.from_user.id != owner_id and not _is_authorized(cq.from_user.id):
        return await cq.answer("🚫 Tumhara session nahi hai!", show_alert=True)

    session = _scrape_sessions.get(owner_id)
    if not session:
        return await cq.answer("⚠️ Session expired ho gaya.", show_alert=True)

    await cq.answer("🚀 Shuru ho gaya!")

    session["running"] = True

    status_msg = session["status_msg"]
    await status_msg.edit_text(
        "🚀 <b>Scraping shuru ho gayi!</b>\n\n"
        "⏳ Progress yahan dikhta rahega...\n\n"
        "<i>/wstop se band karo.</i>",
        reply_markup=None,
        parse_mode="html",
    )

    # Task shuru karo
    task = asyncio.create_task(
        _scrape_loop(
            userbot=session["userbot"],
            channel=session["channel"],
            approve_mode=session["approve_mode"],
            logger_id=session["logger_id"],
            status_msg=status_msg,
            user_id=owner_id,
        )
    )
    session["task"] = task
    log.info(f"Scrape task started for user {owner_id}")


@app.on_callback_query(filters.regex(r"^wstart_cancel_(\d+)$"))
async def cb_wstart_cancel(client: Client, cq: CallbackQuery):
    owner_id = int(cq.matches[0].group(1))

    if cq.from_user.id != owner_id and not _is_authorized(cq.from_user.id):
        return await cq.answer("🚫 Tumhara session nahi hai!", show_alert=True)

    session = _scrape_sessions.pop(owner_id, None)
    if session:
        try:
            await session["userbot"].stop()
        except Exception:
            pass

    await cq.answer("❌ Cancel!")
    await cq.message.edit_text(
        "❌ <b>Scraping cancel kar di.</b>\n\n"
        "Dobara shuru karne ke liye /wstart karo.",
        parse_mode="html",
    )


# ══════════════════════════════════════════════════════════════════════════════
#  /wstop COMMAND
# ══════════════════════════════════════════════════════════════════════════════

@app.on_message(filters.command("wstop") & filters.private)
async def cmd_wstop(client: Client, message: Message):
    user_id = message.from_user.id

    if not _is_authorized(user_id):
        return await message.reply_text("🚫 Permission nahi hai.", parse_mode="html")

    session = _scrape_sessions.get(user_id)
    if not session:
        return await message.reply_text(
            "⚠️ <b>Koi scrape session nahi chal raha.</b>",
            parse_mode="html",
        )

    session["running"] = False

    await message.reply_text(
        "⏹ <b>Scraping band ho rahi hai...</b>\n"
        "<i>Current waifu process hone ke baad rukegi.</i>",
        parse_mode="html",
    )
    log.info(f"/wstop by user {user_id}")
      
