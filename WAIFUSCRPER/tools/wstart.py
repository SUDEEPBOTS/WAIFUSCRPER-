import asyncio
import os
import random

from pyrogram import Client, filters, enums
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

_scrape_sessions: dict[int, dict] = {}

_pending: dict[str, asyncio.Event] = {}
_results: dict[str, bool] = {}

PROGRESS_EVERY = 10


def _is_authorized(user_id: int) -> bool:
    return user_id == config.OWNER_ID or user_id in config.SUDO_USERS


async def _get_userbot() -> Client | None:
    session_string = await get_string_session()
    if not session_string:
        return None

    userbot = Client(
        name="userbot_scraper",
        api_id=config.API_ID,
        api_hash=config.API_HASH,
        session_string=session_string,
        no_updates=True,
    )
    await userbot.start()
    return userbot


async def _count_photos(userbot: Client, channel) -> int:
    count = 0
    async for msg in userbot.get_chat_history(channel):
        if msg.photo:
            count += 1
    return count


def _approve_keyboard(key: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ approve",  callback_data=f"wapprove_{key}"),
            InlineKeyboardButton("❌ skip",     callback_data=f"wskip_{key}"),
        ]
    ])


async def _ask_approve(logger_id: int, userbot: Client, userbot_msg: Message, parsed: dict) -> bool:
    """
    send waifu to logger group and wait for approve/skip.
    returns true = approved, false = skipped.
    """
    caption = (
        f"🆕 <b>new waifu — approve?</b>\n\n"
        f"📛 <b>name:</b>  {parsed.get('name', 'unknown')}\n"
        f"🎭 <b>series:</b>  {parsed.get('series', 'unknown')}\n"
        f"⭐ <b>rarity:</b>  {parsed.get('rarity', 'unknown')}\n"
        f"🆔 <b>id:</b>  {parsed.get('waifu_id', 'auto')}\n"
        f"👤 <b>added by:</b>  {parsed.get('added_by', 'unknown')}\n"
    )

    photo_path = await userbot.download_media(userbot_msg.photo)

    try:
        sent = await app.send_photo(
            chat_id=logger_id,
            photo=photo_path,
            caption=caption,
            parse_mode=enums.ParseMode.HTML,
        )
    except Exception as e:
        log.error(f"approve photo send error: {e}")
        if os.path.exists(photo_path):
            os.remove(photo_path)
        return False

    if os.path.exists(photo_path):
        os.remove(photo_path)

    key = str(sent.id)
    await sent.edit_reply_markup(_approve_keyboard(key))

    event = asyncio.Event()
    _pending[key] = event

    try:
        await asyncio.wait_for(event.wait(), timeout=300)
        return _results.pop(key, False)
    except asyncio.TimeoutError:
        log.warning(f"approve timeout — key={key} ({parsed.get('name')})")
        _pending.pop(key, None)
        _results.pop(key, None)
        try:
            await sent.edit_caption(
                caption + "\n\n⏰ <i>timeout — skipped.</i>",
                parse_mode=enums.ParseMode.HTML,
            )
            await sent.edit_reply_markup(None)
        except Exception:
            pass
        return False


@app.on_callback_query(filters.regex(r"^w(approve|skip)_(\d+)$"))
async def cb_approve_skip(client: Client, cq: CallbackQuery):
    if not _is_authorized(cq.from_user.id):
        return await cq.answer("🚫 permission denied!", show_alert=True)

    action = cq.matches[0].group(1)
    key    = cq.matches[0].group(2)

    if key not in _pending:
        return await cq.answer("⚠️ this request has expired.", show_alert=True)

    approved = action == "approve"
    _results[key] = approved
    _pending[key].set()

    label = "✅ approved" if approved else "❌ skipped"
    await cq.answer(label)

    try:
        original_caption = cq.message.caption or ""
        await cq.message.edit_caption(
            original_caption + f"\n\n<b>{label} by {cq.from_user.first_name}</b>",
            parse_mode=enums.ParseMode.HTML,
        )
        await cq.message.edit_reply_markup(None)
    except Exception:
        pass


async def _scrape_loop(
    userbot: Client,
    channel,
    approve_mode: bool,
    logger_id: int | None,
    status_msg: Message,
    user_id: int,
) -> None:
    total     = 0
    saved     = 0
    skipped   = 0
    errors    = 0
    processed = 0

    try:
        async for msg in userbot.get_chat_history(channel):

            session = _scrape_sessions.get(user_id, {})
            if not session.get("running", True):
                log.info(f"scrape stopped by user {user_id}")
                break

            if not msg.photo:
                continue

            total += 1

            try:
                if approve_mode and logger_id:
                    from WAIFUSCRPER.tools.dwonloder.Dwonlod import parse_caption
                    parsed = parse_caption(msg.caption or "")

                    if not parsed:
                        skipped += 1
                        continue

                    approved = await _ask_approve(logger_id, userbot, msg, parsed)
                    if not approved:
                        skipped += 1
                        continue

                result = await process_waifu_message(userbot, msg)

                if result:
                    saved += 1
                    log.success(f"[{saved}] saved → {result.get('name')} | {result.get('rarity')}")
                else:
                    skipped += 1

            except FloodWait as e:
                wait_time = e.value + 2
                log.warning(f"floodwait! waiting for {wait_time}s...")
                await asyncio.sleep(wait_time)
            except Exception as e:
                log.error(f"error on msg {msg.id}: {e}")
                errors += 1

            processed += 1

            if processed % PROGRESS_EVERY == 0:
                try:
                    await status_msg.edit_text(
                        f"⏳ <b>scraping in progress...</b>\n\n"
                        f"📊 <b>processed:</b>  {processed}\n"
                        f"✅ <b>saved:</b>      {saved}\n"
                        f"⏭ <b>skipped:</b>    {skipped}\n"
                        f"❌ <b>errors:</b>     {errors}\n\n"
                        f"<i>use /wstop to stop.</i>",
                        parse_mode=enums.ParseMode.HTML,
                    )
                except Exception:
                    pass

            gap = random.uniform(1.0, 2.0)
            log.info(f"sleeping for {gap:.2f}s...")
            await asyncio.sleep(gap)

    except Exception as e:
        log.error(f"scrape loop crashed: {e}")

    finally:
        try:
            await userbot.stop()
        except Exception:
            pass

        _scrape_sessions.pop(user_id, None)

        try:
            await status_msg.edit_text(
                f"🎉 <b>scraping complete!</b>\n\n"
                f"📊 <b>total scanned:</b>  {processed}\n"
                f"✅ <b>saved:</b>          {saved}\n"
                f"⏭ <b>skipped:</b>        {skipped}\n"
                f"❌ <b>errors:</b>         {errors}\n\n"
                f"<i>{saved} new waifus added to mongodb.</i>",
                parse_mode=enums.ParseMode.HTML,
            )
        except Exception:
            pass

        log.info(f"scrape done — {saved} saved / {skipped} skipped / {errors} errors (user={user_id})")


@app.on_message(filters.command("wstart") & filters.private)
async def cmd_wstart(client: Client, message: Message):
    user_id = message.from_user.id

    if not _is_authorized(user_id):
        return await message.reply_text("🚫 <b>only owner can use this.</b>", parse_mode=enums.ParseMode.HTML)

    if user_id in _scrape_sessions:
        return await message.reply_text("⚠️ <b>a session is already running!</b>\nuse /wstop first.", parse_mode=enums.ParseMode.HTML)

    wait = await message.reply_text("🔍 checking config...", parse_mode=enums.ParseMode.HTML)

    target_channel = await get_target_channel()
    if not target_channel:
        return await wait.edit_text("❌ <b>target channel not set!</b>", parse_mode=enums.ParseMode.HTML)

    string_session = await get_string_session()
    if not string_session:
        return await wait.edit_text("❌ <b>string session not set!</b>", parse_mode=enums.ParseMode.HTML)

    approve_mode = await get_approve_mode()
    logger_id    = await get_logger() if approve_mode else None

    if approve_mode and not logger_id:
        return await wait.edit_text("❌ <b>logger id not set!</b>", parse_mode=enums.ParseMode.HTML)

    await wait.edit_text("🔌 connecting userbot...", parse_mode=enums.ParseMode.HTML)

    userbot = await _get_userbot()
    if not userbot:
        return await wait.edit_text("❌ <b>userbot failed to connect.</b>", parse_mode=enums.ParseMode.HTML)

    await wait.edit_text("📡 scanning channel and counting photos...", parse_mode=enums.ParseMode.HTML)

    try:
        chat = await userbot.get_chat(target_channel)
    except Exception as e:
        await userbot.stop()
        return await wait.edit_text(f"❌ <b>error:</b> <code>{e}</code>", parse_mode=enums.ParseMode.HTML)

    try:
        photo_count = await _count_photos(userbot, target_channel)
    except Exception as e:
        await userbot.stop()
        return await wait.edit_text(f"❌ <b>count error:</b> <code>{e}</code>", parse_mode=enums.ParseMode.HTML)

    await wait.edit_text(
        f"📋 <b>channel info</b>\n\n"
        f"📣 <b>channel:</b>  {chat.title}\n"
        f"🖼 <b>waifu photos:</b>  <code>{photo_count}</code>\n"
        f"✅ <b>approve mode:</b>  {'on 🟢' if approve_mode else 'off 🔴'}\n\n"
        f"<b>start scraping?</b>",
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton("✅ yes, start!", callback_data=f"wstart_confirm_{user_id}"),
                InlineKeyboardButton("❌ no",          callback_data=f"wstart_cancel_{user_id}"),
            ]
        ]),
        parse_mode=enums.ParseMode.HTML,
    )

    _scrape_sessions[user_id] = {
        "running":      False,
        "userbot":      userbot,
        "channel":      target_channel,
        "approve_mode": approve_mode,
        "logger_id":    logger_id,
        "status_msg":   wait,
        "task":         None,
    }


@app.on_callback_query(filters.regex(r"^wstart_confirm_(\d+)$"))
async def cb_wstart_confirm(client: Client, cq: CallbackQuery):
    owner_id = int(cq.matches[0].group(1))

    if cq.from_user.id != owner_id and not _is_authorized(cq.from_user.id):
        return await cq.answer("🚫 not your session!", show_alert=True)

    session = _scrape_sessions.get(owner_id)
    if not session:
        return await cq.answer("⚠️ session expired.", show_alert=True)

    await cq.answer("🚀 starting!")
    session["running"] = True
    status_msg = session["status_msg"]

    await status_msg.edit_text(
        "🚀 <b>scraping started!</b>\n⏳ progress will appear here...\n<i>use /wstop to stop.</i>",
        reply_markup=None,
        parse_mode=enums.ParseMode.HTML,
    )

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


@app.on_callback_query(filters.regex(r"^wstart_cancel_(\d+)$"))
async def cb_wstart_cancel(client: Client, cq: CallbackQuery):
    owner_id = int(cq.matches[0].group(1))

    if cq.from_user.id != owner_id and not _is_authorized(cq.from_user.id):
        return await cq.answer("🚫 permission denied!", show_alert=True)

    session = _scrape_sessions.pop(owner_id, None)
    if session:
        try:
            await session["userbot"].stop()
        except Exception:
            pass

    await cq.answer("❌ cancelled!")
    await cq.message.edit_text("❌ <b>scraping cancelled.</b>", parse_mode=enums.ParseMode.HTML)


@app.on_message(filters.command("wstop") & filters.private)
async def cmd_wstop(client: Client, message: Message):
    user_id = message.from_user.id

    if not _is_authorized(user_id):
        return await message.reply_text("🚫 permission denied.", parse_mode=enums.ParseMode.HTML)

    session = _scrape_sessions.get(user_id)
    if not session:
        return await message.reply_text("⚠️ <b>no active scrape session found.</b>", parse_mode=enums.ParseMode.HTML)

    session["running"] = False
    await message.reply_text(
        "⏹ <b>stopping scrape...</b>\n<i>will stop after current waifu.</i>",
        parse_mode=enums.ParseMode.HTML,
  )
  
