import asyncio
import random

from pyrogram import Client, filters, enums
from pyrogram.errors import FloodWait
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
    get_sudo_users,
    waifu_exists,
)
from WAIFUSCRPER.tools.dwonloder.Dwonlod import (
    parse_caption,
    download_photo,
    upload_image,
    save_waifu,
)

log = LOGGER(__name__)

_scrape_sessions: dict[int, dict] = {}
_pending:         dict[str, asyncio.Event] = {}
_results:         dict[str, bool] = {}

PROGRESS_EVERY = 10


async def _is_authorized(user_id: int) -> bool:
    if user_id == config.OWNER_ID:
        return True
    if user_id in config.SUDO_USERS:
        return True
    db_sudos = await get_sudo_users()
    return user_id in db_sudos


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


def _approve_keyboard(key: str, img_url: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ 𝐀ᴘᴘʀᴏᴠᴇ", callback_data=f"wapprove_{key}"),
            InlineKeyboardButton("❌ 𝚂ᴋɪᴘ",    callback_data=f"wskip_{key}"),
        ],
        [
            # view button — browser mein khulta hai
            InlineKeyboardButton("🖼 𝚅𝚒𝚎𝚠 𝚆𝚊𝚒𝚏𝚞", url=img_url),
        ],
    ])


async def _ask_approve(logger_id: int, parsed: dict, img_url: str) -> bool:
    """
    send_message with plain catbox URL at top → Telegram auto preview (image).
    SendMedia = 0, no extra EditMessage for buttons = fast, no flood.
    """
    text = (
        f"{img_url}\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"🆕 <b>𝙽𝚎𝚠 𝚆𝚊𝚒𝚏𝚞 — 𝙰𝚙𝚙𝚛𝚘𝚟𝚎?</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"📛 <b>𝙽𝚊𝚖𝚎 :</b>   {parsed.get('name', 'unknown')}\n"
        f"🎭 <b>𝚂𝚎𝚛𝚒𝚎𝚜 :</b> {parsed.get('series', 'unknown')}\n"
        f"⭐ <b>𝚁𝚊𝚛𝚒𝚝𝚢 :</b> {parsed.get('rarity', 'unknown')}\n"
        f"🆔 <b>𝙸𝙳 :</b>     {parsed.get('waifu_id', 'auto')}\n"
        f"👤 <b>𝙱𝚢 :</b>     {parsed.get('added_by', 'unknown')}\n"
    )

    try:
        sent = await app.send_message(
            chat_id=logger_id,
            text=text,
            parse_mode=enums.ParseMode.HTML,
            reply_markup=_approve_keyboard("PLACEHOLDER", img_url),
            disable_web_page_preview=False,
        )
    except Exception as e:
        log.error(f"approve message send error: {e}")
        return False

    key = str(sent.id)
    try:
        await sent.edit_reply_markup(_approve_keyboard(key, img_url))
    except Exception:
        pass

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
            await sent.edit_text(
                text + "\n⏰ <i>𝚃𝚒𝚖𝚎𝚘𝚞𝚝 — 𝚂𝚔𝚒𝚙𝚙𝚎𝚍.</i>",
                parse_mode=enums.ParseMode.HTML,
                reply_markup=None,
                disable_web_page_preview=False,
            )
        except Exception:
            pass
        return False


@app.on_callback_query(filters.regex(r"^w(approve|skip)_(\d+)$"))
async def cb_approve_skip(client: Client, cq: CallbackQuery):
    if not await _is_authorized(cq.from_user.id):
        return await cq.answer("🚫 𝙿𝚎𝚛𝚖𝚒𝚜𝚜𝚒𝚘𝚗 𝙳𝚎𝚗𝚒𝚎𝚍!", show_alert=True)

    action = cq.matches[0].group(1)
    key    = cq.matches[0].group(2)

    if key not in _pending:
        return await cq.answer("⚠️ 𝚁𝚎𝚚𝚞𝚎𝚜𝚝 𝙴𝚡𝚙𝚒𝚛𝚎𝚍.", show_alert=True)

    approved      = action == "approve"
    _results[key] = approved
    _pending[key].set()

    label = "✅ 𝙰𝚙𝚙𝚛𝚘𝚟𝚎𝚍" if approved else "❌ 𝚂𝚔𝚒𝚙𝚙𝚎𝚍"
    await cq.answer(label)

    try:
        original_text = cq.message.text or ""
        await cq.message.edit_text(
            original_text + f"\n\n<b>{label} 𝚋𝚢 {cq.from_user.first_name}</b>",
            parse_mode=enums.ParseMode.HTML,
            reply_markup=None,
            disable_web_page_preview=False,
        )
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
                # step 1: caption parse
                parsed = parse_caption(msg.caption or "")
                if not parsed:
                    skipped += 1
                    continue

                # ✅ step 2: early duplicate check (download/upload waste nahi)
                if parsed.get("waifu_id"):
                    if await waifu_exists(parsed["waifu_id"]):
                        log.info(f"duplicate early skip → {parsed['waifu_id']} ({parsed['name']})")
                        skipped += 1
                        continue

                # step 3: photo download
                data, fname = await download_photo(userbot, msg)
                if not data:
                    errors += 1
                    continue

                # step 4: catbox/imgbb upload (retry logic Dwonlod.py mein)
                img_url = await upload_image(data, fname)
                if not img_url:
                    log.error(f"upload failed for msg {msg.id} — skipping")
                    errors += 1
                    continue

                # step 5: approve (agar mode on hai)
                if approve_mode and logger_id:
                    approved = await _ask_approve(logger_id, parsed, img_url)
                    if not approved:
                        skipped += 1
                        continue

                # step 6: DB save
                saved_ok = await save_waifu(parsed, img_url, source_message_id=msg.id)
                if saved_ok:
                    saved += 1
                    log.success(f"[{saved}] saved → {parsed.get('name')} | {parsed.get('rarity')}")
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
                        f"⏳ <b>𝚂𝚌𝚛𝚊𝚙𝚒𝚗𝚐 𝚒𝚗 𝙿𝚛𝚘𝚐𝚛𝚎𝚜𝚜...</b>\n\n"
                        f"📊 <b>𝙿𝚛𝚘𝚌𝚎𝚜𝚜𝚎𝚍 :</b>  {processed}\n"
                        f"✅ <b>𝚂𝚊𝚟𝚎𝚍 :</b>      {saved}\n"
                        f"⏭ <b>𝚂𝚔𝚒𝚙𝚙𝚎𝚍 :</b>    {skipped}\n"
                        f"❌ <b>𝙴𝚛𝚛𝚘𝚛𝚜 :</b>     {errors}\n\n"
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
                f"🎉 <b>𝚂𝚌𝚛𝚊𝚙𝚒𝚗𝚐 𝙲𝚘𝚖𝚙𝚕𝚎𝚝𝚎!</b>\n\n"
                f"📊 <b>𝚃𝚘𝚝𝚊𝚕 𝚂𝚌𝚊𝚗𝚗𝚎𝚍 :</b>  {processed}\n"
                f"✅ <b>𝚂𝚊𝚟𝚎𝚍 :</b>          {saved}\n"
                f"⏭ <b>𝚂𝚔𝚒𝚙𝚙𝚎𝚍 :</b>        {skipped}\n"
                f"❌ <b>𝙴𝚛𝚛𝚘𝚛𝚜 :</b>         {errors}\n\n"
                f"<i>{saved} new waifus added to mongodb.</i>",
                parse_mode=enums.ParseMode.HTML,
            )
        except Exception:
            pass

        log.info(f"scrape done — {saved} saved / {skipped} skipped / {errors} errors (user={user_id})")


@app.on_message(filters.command("wstart") & filters.private)
async def cmd_wstart(client: Client, message: Message):
    user_id = message.from_user.id

    if not await _is_authorized(user_id):
        return await message.reply_text("🚫 <b>𝙾𝚗𝚕𝚢 𝙾𝚠𝚗𝚎𝚛/𝚂𝚞𝚍𝚘 𝚌𝚊𝚗 𝚞𝚜𝚎 𝚝𝚑𝚒𝚜.</b>", parse_mode=enums.ParseMode.HTML)

    if user_id in _scrape_sessions:
        return await message.reply_text("⚠️ <b>𝙰 𝚜𝚎𝚜𝚜𝚒𝚘𝚗 𝚒𝚜 𝚊𝚕𝚛𝚎𝚊𝚍𝚢 𝚛𝚞𝚗𝚗𝚒𝚗𝚐!</b>\nuse /wstop first.", parse_mode=enums.ParseMode.HTML)

    wait = await message.reply_text("🔍 checking config...", parse_mode=enums.ParseMode.HTML)

    target_channel = await get_target_channel()
    if not target_channel:
        return await wait.edit_text("❌ <b>𝚃𝚊𝚛𝚐𝚎𝚝 𝚌𝚑𝚊𝚗𝚗𝚎𝚕 𝚗𝚘𝚝 𝚜𝚎𝚝!</b>", parse_mode=enums.ParseMode.HTML)

    string_session = await get_string_session()
    if not string_session:
        return await wait.edit_text("❌ <b>𝚂𝚝𝚛𝚒𝚗𝚐 𝚜𝚎𝚜𝚜𝚒𝚘𝚗 𝚗𝚘𝚝 𝚜𝚎𝚝!</b>", parse_mode=enums.ParseMode.HTML)

    approve_mode = await get_approve_mode()
    logger_id    = await get_logger() if approve_mode else None

    if approve_mode and not logger_id:
        return await wait.edit_text("❌ <b>𝙻𝚘𝚐𝚐𝚎𝚛 𝙸𝙳 𝚗𝚘𝚝 𝚜𝚎𝚝!</b>", parse_mode=enums.ParseMode.HTML)

    await wait.edit_text("🔌 connecting userbot...", parse_mode=enums.ParseMode.HTML)

    userbot = await _get_userbot()
    if not userbot:
        return await wait.edit_text("❌ <b>𝚄𝚜𝚎𝚛𝚋𝚘𝚝 𝚏𝚊𝚒𝚕𝚎𝚍 𝚝𝚘 𝚌𝚘𝚗𝚗𝚎𝚌𝚝.</b>", parse_mode=enums.ParseMode.HTML)

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
        f"📋 <b>𝙲𝚑𝚊𝚗𝚗𝚎𝚕 𝙸𝚗𝚏𝚘</b>\n\n"
        f"📣 <b>𝙲𝚑𝚊𝚗𝚗𝚎𝚕 :</b>       {chat.title}\n"
        f"🖼 <b>𝚆𝚊𝚒𝚏𝚞 𝙿𝚑𝚘𝚝𝚘𝚜 :</b>  <code>{photo_count}</code>\n"
        f"✅ <b>𝙰𝚙𝚙𝚛𝚘𝚟𝚎 𝙼𝚘𝚍𝚎 :</b>  {'on 🟢' if approve_mode else 'off 🔴'}\n\n"
        f"<b>𝚂𝚝𝚊𝚛𝚝 𝚜𝚌𝚛𝚊𝚙𝚒𝚗𝚐?</b>",
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton("✅ 𝚈𝚎𝚜, 𝚂𝚝𝚊𝚛𝚝!", callback_data=f"wstart_confirm_{user_id}"),
                InlineKeyboardButton("❌ 𝙽𝚘",          callback_data=f"wstart_cancel_{user_id}"),
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

    if cq.from_user.id != owner_id and not await _is_authorized(cq.from_user.id):
        return await cq.answer("🚫 𝙽𝚘𝚝 𝚢𝚘𝚞𝚛 𝚜𝚎𝚜𝚜𝚒𝚘𝚗!", show_alert=True)

    session = _scrape_sessions.get(owner_id)
    if not session:
        return await cq.answer("⚠️ 𝚂𝚎𝚜𝚜𝚒𝚘𝚗 𝚎𝚡𝚙𝚒𝚛𝚎𝚍.", show_alert=True)

    await cq.answer("🚀 Starting!")
    session["running"] = True
    status_msg = session["status_msg"]

    await status_msg.edit_text(
        "🚀 <b>𝚂𝚌𝚛𝚊𝚙𝚒𝚗𝚐 𝚂𝚝𝚊𝚛𝚝𝚎𝚍!</b>\n⏳ progress will appear here...\n<i>use /wstop to stop.</i>",
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

    if cq.from_user.id != owner_id and not await _is_authorized(cq.from_user.id):
        return await cq.answer("🚫 𝙿𝚎𝚛𝚖𝚒𝚜𝚜𝚒𝚘𝚗 𝙳𝚎𝚗𝚒𝚎𝚍!", show_alert=True)

    session = _scrape_sessions.pop(owner_id, None)
    if session:
        try:
            await session["userbot"].stop()
        except Exception:
            pass

    await cq.answer("❌ Cancelled!")
    await cq.message.edit_text("❌ <b>𝚂𝚌𝚛𝚊𝚙𝚒𝚗𝚐 𝙲𝚊𝚗𝚌𝚎𝚕𝚕𝚎𝚍.</b>", parse_mode=enums.ParseMode.HTML)


@app.on_message(filters.command("wstop") & filters.private)
async def cmd_wstop(client: Client, message: Message):
    user_id = message.from_user.id

    if not await _is_authorized(user_id):
        return await message.reply_text("🚫 𝙿𝚎𝚛𝚖𝚒𝚜𝚜𝚒𝚘𝚗 𝙳𝚎𝚗𝚒𝚎𝚍.", parse_mode=enums.ParseMode.HTML)

    session = _scrape_sessions.get(user_id)
    if not session:
        return await message.reply_text("⚠️ <b>𝙽𝚘 𝚊𝚌𝚝𝚒𝚟𝚎 𝚜𝚎𝚜𝚜𝚒𝚘𝚗 𝚏𝚘𝚞𝚗𝚍.</b>", parse_mode=enums.ParseMode.HTML)

    session["running"] = False
    await message.reply_text(
        "⏹ <b>𝚂𝚝𝚘𝚙𝚙𝚒𝚗𝚐 𝚂𝚌𝚛𝚊𝚙𝚎...</b>\n<i>will stop after current waifu.</i>",
        parse_mode=enums.ParseMode.HTML,
            )
    
