import asyncio

from pyrogram import Client, filters, enums
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


def _is_owner(user_id: int) -> bool:
    return user_id == config.OWNER_ID

def _is_authorized(user_id: int) -> bool:
    return user_id == config.OWNER_ID or user_id in config.SUDO_USERS


def _kb_p1() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("˹ 𝐒єᴛ 𝐋ᴏɢɢєʀ ˼",         callback_data="cfg_set_logger"),
            InlineKeyboardButton("˹ 𝐀ᴘᴘʀᴏᴠє 𝐌ᴏᴅє ˼",        callback_data="cfg_set_approve"),
        ],
        [
            InlineKeyboardButton("˹ 𝐒єᴛ 𝐒єssιᴏη ˼",         callback_data="cfg_set_session"),
        ],
        [
            InlineKeyboardButton("˹ 𝐂ᴀᴘᴛιᴏη 𝐊єʏᴡᴏʀᴅ ˼",     callback_data="cfg_set_keyword"),
            InlineKeyboardButton("˹ 𝐂ᴏʟʟєᴄᴛιᴏη ˼",           callback_data="cfg_set_collection"),
        ],
        [
            InlineKeyboardButton("˹ 𝚮ᴏϻє ˼",                 callback_data="menu_home"),
            InlineKeyboardButton("˹ 𝐍єхᴛ ▶️ ˼",              callback_data="menu_config_p2"),
        ],
    ])


def _kb_p2() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("˹ 𝐑ϻ 𝐒єssιᴏη ˼",           callback_data="cfg_rm_session"),
            InlineKeyboardButton("˹ 𝐑ϻ 𝐋ᴏɢɢєʀ ˼",            callback_data="cfg_rm_logger"),
        ],
        [
            InlineKeyboardButton("˹ 𝐑ϻ 𝐂ᴏʟʟєᴄᴛιᴏη ˼",        callback_data="cfg_rm_collection"),
            InlineKeyboardButton("˹ 𝐑ϻ 𝚮ᴀιғᴜ ˼",              callback_data="cfg_rm_waifu"),
        ],
        [
            InlineKeyboardButton("˹ 𝐓ᴀʀɢєᴛ 𝐂нᴀηηєʟ ˼",       callback_data="cfg_set_target"),
            InlineKeyboardButton("˹ 𝐅єᴛᴄн 𝐀ʟʟ ˼",             callback_data="cfg_fetch_all"),
        ],
        [
            InlineKeyboardButton("˹ 𝐊єʏ 𝐌єssᴀɢє ˼",           callback_data="cfg_set_keymsg"),
        ],
        [
            InlineKeyboardButton("˹ ◀️ 𝐁ᴀᴄᴋ ˼",              callback_data="menu_config_p1"),
            InlineKeyboardButton("˹ 𝚮ᴏϻє ˼",                 callback_data="menu_home"),
            InlineKeyboardButton("˹ 𝐍єхᴛ ▶️ ˼",              callback_data="menu_config_p3"),
        ],
    ])


def _kb_p3() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("˹ 𝐓ᴏɢɢʟє 𝐀ᴜᴛᴏ 𝐅єᴛᴄн ˼",    callback_data="cfg_toggle_autofetch"),
        ],
        [
            InlineKeyboardButton("˹ ◀️ 𝐁ᴀᴄᴋ ˼",              callback_data="menu_config_p2"),
            InlineKeyboardButton("˹ 𝚮ᴏϻє ˼",                 callback_data="menu_home"),
        ],
    ])

def _kb_home() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("˹ 𝚮ᴏϻє ˼", callback_data="menu_home")],
    ])

def _kb_cancel() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("˹ ❌ 𝐂ᴀηᴄєʟ ˼", callback_data="cfg_cancel_input")],
    ])


async def _show_p1(msg_or_cq):
    text = (
        "⚙️ <b>ᴄᴏηғιɢ — ᴘᴀɢє 1 (sєᴛᴜᴘ)</b>\n\n"
        "choose a setting below:"
    )
    if isinstance(msg_or_cq, CallbackQuery):
        await msg_or_cq.message.edit_text(text, reply_markup=_kb_p1(), parse_mode=enums.ParseMode.HTML)
    else:
        await msg_or_cq.reply_text(text, reply_markup=_kb_p1(), parse_mode=enums.ParseMode.HTML)


async def _show_p2(cq: CallbackQuery):
    text = (
        "⚙️ <b>ᴄᴏηғιɢ — ᴘᴀɢє 2 (ʀєϻᴏᴠє / ᴛᴀʀɢєᴛ)</b>\n\n"
        "choose an option below:"
    )
    await cq.message.edit_text(text, reply_markup=_kb_p2(), parse_mode=enums.ParseMode.HTML)


async def _show_p3(cq: CallbackQuery):
    auto = await get_auto_fetch()
    status = "🟢 on" if auto else "🔴 off"
    text = (
        f"⚙️ <b>ᴄᴏηғιɢ — ᴘᴀɢє 3 (ᴀᴜᴛᴏ ғєᴛᴄн)</b>\n\n"
        f"🔄 <b>ᴀᴜᴛᴏ ғєᴛᴄн ηєᴡ ᴡᴀιғᴜs:</b>  {status}\n\n"
        "press the button to toggle:"
    )
    await cq.message.edit_text(text, reply_markup=_kb_p3(), parse_mode=enums.ParseMode.HTML)


@app.on_message(filters.command("config") & filters.private)
async def cmd_config(client: Client, message: Message):
    if not _is_authorized(message.from_user.id):
        return await message.reply_text("🚫 permission denied!", parse_mode=enums.ParseMode.HTML)
    await _show_p1(message)


@app.on_callback_query(filters.regex("^menu_config_p1$"))
async def cb_config_p1(client: Client, cq: CallbackQuery):
    if not _is_authorized(cq.from_user.id):
        return await cq.answer("🚫 permission denied!", show_alert=True)
    await cq.answer()
    await _show_p1(cq)


@app.on_callback_query(filters.regex("^menu_config_p2$"))
async def cb_config_p2(client: Client, cq: CallbackQuery):
    if not _is_authorized(cq.from_user.id):
        return await cq.answer("🚫 permission denied!", show_alert=True)
    await cq.answer()
    await _show_p2(cq)


@app.on_callback_query(filters.regex("^menu_config_p3$"))
async def cb_config_p3(client: Client, cq: CallbackQuery):
    if not _is_authorized(cq.from_user.id):
        return await cq.answer("🚫 permission denied!", show_alert=True)
    await cq.answer()
    await _show_p3(cq)


_awaiting: dict[int, str] = {}


@app.on_callback_query(filters.regex("^cfg_cancel_input$"))
async def cb_cancel_input(client: Client, cq: CallbackQuery):
    _awaiting.pop(cq.from_user.id, None)
    await cq.answer("cancelled ✅")
    await _show_p1(cq)


@app.on_message(filters.private & filters.text & ~filters.command(
    ["start","help","config","wstart","wstop","addsudo","rmsudo","sudolist","setsession","cancel"]
), group=1)
async def cfg_text_listener(client: Client, message: Message):
    uid   = message.from_user.id
    state = _awaiting.get(uid)
    if not state:
        return

    text = message.text.strip()
    _awaiting.pop(uid, None)

    if state == "set_logger":
        try:
            chat_id = int(text)
            await set_logger(chat_id)
            await message.reply_text(
                f"✅ <b>ʟᴏɢɢєʀ sєᴛ!</b>\n<code>{chat_id}</code>",
                reply_markup=_kb_home(), parse_mode=enums.ParseMode.HTML,
            )
        except ValueError:
            await message.reply_text(
                "❌ numeric chat id only! (e.g. -100xxxxxxxxxx)",
                reply_markup=_kb_home(), parse_mode=enums.ParseMode.HTML,
            )

    elif state == "set_collection":
        await set_collection_name(text)
        await message.reply_text(
            f"✅ <b>ᴄᴏʟʟєᴄᴛιᴏη ηᴀϻє sєᴛ:</b>  <code>{text}</code>",
            reply_markup=_kb_home(), parse_mode=enums.ParseMode.HTML,
        )

    elif state == "set_keyword":
        from WAIFUSCRPER.Database.Mangodb import _set_config
        await _set_config("rarity_keyword", text)
        await message.reply_text(
            f"✅ <b>ᴄᴀᴘᴛιᴏη ᴋєʏᴡᴏʀᴅ sєᴛ:</b>  <code>{text}</code>",
            reply_markup=_kb_home(), parse_mode=enums.ParseMode.HTML,
        )

    elif state == "set_target":
        try:
            try:
                val = int(text)
            except ValueError:
                val = text
            await set_target_channel(val)
            await message.reply_text(
                f"✅ <b>ᴛᴀʀɢєᴛ ᴄнᴀηηєʟ sєᴛ:</b>  <code>{val}</code>",
                reply_markup=_kb_home(), parse_mode=enums.ParseMode.HTML,
            )
        except Exception as e:
            await message.reply_text(
                f"❌ error: <code>{e}</code>",
                reply_markup=_kb_home(), parse_mode=enums.ParseMode.HTML,
            )

    elif state == "rm_waifu":
        deleted = await remove_waifu_by_id(text)
        if deleted:
            await message.reply_text(
                f"✅ <b>ᴡᴀιғᴜ ᴅєʟєᴛєᴅ!</b>  id: <code>{text}</code>",
                reply_markup=_kb_home(), parse_mode=enums.ParseMode.HTML,
            )
        else:
            await message.reply_text(
                f"❌ <b>ᴡᴀιғᴜ ηᴏᴛ ғᴏᴜηᴅ.</b>  id: <code>{text}</code>",
                reply_markup=_kb_home(), parse_mode=enums.ParseMode.HTML,
            )

    elif state == "set_keymsg":
        await set_keyboard_message(text)
        await message.reply_text(
            f"✅ <b>ᴋєʏʙᴏᴀʀᴅ ϻєssᴀɢє sєᴛ!</b>\n\n{text}",
            reply_markup=_kb_home(), parse_mode=enums.ParseMode.HTML,
        )


@app.on_callback_query(filters.regex("^cfg_set_logger$"))
async def cb_set_logger(client: Client, cq: CallbackQuery):
    if not _is_authorized(cq.from_user.id):
        return await cq.answer("🚫 permission denied!", show_alert=True)
    await cq.answer()
    _awaiting[cq.from_user.id] = "set_logger"
    current = await get_logger()
    await cq.message.edit_text(
        f"📋 <b>sєᴛ ʟᴏɢɢєʀ</b>\n\n"
        f"current: <code>{current or 'not set'}</code>\n\n"
        "send the <b>numeric id</b> of your log group/channel:\n"
        "<i>(e.g. -100xxxxxxxxxx)</i>",
        reply_markup=_kb_cancel(), parse_mode=enums.ParseMode.HTML,
    )


@app.on_callback_query(filters.regex("^cfg_set_approve$"))
async def cb_set_approve(client: Client, cq: CallbackQuery):
    if not _is_authorized(cq.from_user.id):
        return await cq.answer("🚫 permission denied!", show_alert=True)
    await cq.answer()
    current = await get_approve_mode()
    new_val = not current
    await set_approve_mode(new_val)
    status = "🟢 on" if new_val else "🔴 off"
    await cq.message.edit_text(
        f"✅ <b>ᴀᴘᴘʀᴏᴠє ϻᴏᴅє:</b>  {status}\n\n"
        "<i>each waifu will require approval during scraping.</i>",
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton("˹ 🔄 𝐓ᴏɢɢʟє ˼",  callback_data="cfg_set_approve"),
                InlineKeyboardButton("˹ 𝚮ᴏϻє ˼",        callback_data="menu_home"),
            ],
        ]),
        parse_mode=enums.ParseMode.HTML,
    )


@app.on_callback_query(filters.regex("^cfg_set_session$"))
async def cb_set_session(client: Client, cq: CallbackQuery):
    if not _is_authorized(cq.from_user.id):
        return await cq.answer("🚫 permission denied!", show_alert=True)
    await cq.answer()
    await cq.message.edit_text(
        "🔐 <b>sᴛʀιηɢ sєssιᴏη sєᴛᴜᴘ</b>\n\n"
        "send /setsession in private or start the flow here.\n\n"
        "<i>flow: phone → otp → 2fa (if enabled) → done</i>",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("˹ ▶️ 𝐒ᴛᴀʀᴛ 𝐅ʟᴏᴡ ˼",  callback_data="cfg_start_session_flow")],
            [InlineKeyboardButton("˹ 𝚮ᴏϻє ˼",            callback_data="menu_home")],
        ]),
        parse_mode=enums.ParseMode.HTML,
    )


@app.on_callback_query(filters.regex("^cfg_start_session_flow$"))
async def cb_start_session_flow(client: Client, cq: CallbackQuery):
    if not _is_authorized(cq.from_user.id):
        return await cq.answer("🚫 permission denied!", show_alert=True)
    await cq.answer()
    await cq.message.reply_text(
        "✅ send <b>/setsession</b> in this chat to begin session setup.",
        parse_mode=enums.ParseMode.HTML,
    )


@app.on_callback_query(filters.regex("^cfg_set_keyword$"))
async def cb_set_keyword(client: Client, cq: CallbackQuery):
    if not _is_authorized(cq.from_user.id):
        return await cq.answer("🚫 permission denied!", show_alert=True)
    await cq.answer()
    _awaiting[cq.from_user.id] = "set_keyword"
    await cq.message.edit_text(
        "🔑 <b>sєᴛ ᴄᴀᴘᴛιᴏη ᴋєʏᴡᴏʀᴅ</b>\n\n"
        "default: <code>rarity</code>\n\n"
        "send the keyword used to find rarity in waifu captions:",
        reply_markup=_kb_cancel(), parse_mode=enums.ParseMode.HTML,
    )


@app.on_callback_query(filters.regex("^cfg_set_collection$"))
async def cb_set_collection(client: Client, cq: CallbackQuery):
    if not _is_authorized(cq.from_user.id):
        return await cq.answer("🚫 permission denied!", show_alert=True)
    await cq.answer()
    _awaiting[cq.from_user.id] = "set_collection"
    current = await get_collection_name()
    await cq.message.edit_text(
        f"🗂 <b>sєᴛ ᴄᴏʟʟєᴄᴛιᴏη ηᴀϻє</b>\n\n"
        f"current: <code>{current or 'waifus (default)'}</code>\n\n"
        "send the mongodb collection name:",
        reply_markup=_kb_cancel(), parse_mode=enums.ParseMode.HTML,
    )


@app.on_callback_query(filters.regex("^cfg_rm_session$"))
async def cb_rm_session(client: Client, cq: CallbackQuery):
    if not _is_authorized(cq.from_user.id):
        return await cq.answer("🚫 permission denied!", show_alert=True)
    await cq.answer()
    await remove_string_session()
    await cq.message.edit_text(
        "✅ <b>sᴛʀιηɢ sєssιᴏη ʀєϻᴏᴠєᴅ!</b>\n\n"
        "use /setsession to set it again.",
        reply_markup=_kb_home(), parse_mode=enums.ParseMode.HTML,
    )


@app.on_callback_query(filters.regex("^cfg_rm_logger$"))
async def cb_rm_logger(client: Client, cq: CallbackQuery):
    if not _is_authorized(cq.from_user.id):
        return await cq.answer("🚫 permission denied!", show_alert=True)
    await cq.answer()
    await remove_logger()
    await cq.message.edit_text(
        "✅ <b>ʟᴏɢɢєʀ ʀєϻᴏᴠєᴅ!</b>",
        reply_markup=_kb_home(), parse_mode=enums.ParseMode.HTML,
    )


@app.on_callback_query(filters.regex("^cfg_rm_collection$"))
async def cb_rm_collection(client: Client, cq: CallbackQuery):
    if not _is_authorized(cq.from_user.id):
        return await cq.answer("🚫 permission denied!", show_alert=True)
    await cq.answer()
    await remove_collection_name()
    await cq.message.edit_text(
        "✅ <b>ᴄᴏʟʟєᴄᴛιᴏη ηᴀϻє ʀєϻᴏᴠєᴅ!</b>\n"
        "<i>default 'waifus' will be used now.</i>",
        reply_markup=_kb_home(), parse_mode=enums.ParseMode.HTML,
    )


@app.on_callback_query(filters.regex("^cfg_rm_waifu$"))
async def cb_rm_waifu(client: Client, cq: CallbackQuery):
    if not _is_authorized(cq.from_user.id):
        return await cq.answer("🚫 permission denied!", show_alert=True)
    await cq.answer()
    _awaiting[cq.from_user.id] = "rm_waifu"
    await cq.message.edit_text(
        "🗑 <b>ʀєϻᴏᴠє ᴡᴀιғᴜ ʙʏ ιᴅ</b>\n\n"
        "send the <b>waifu_id</b> you want to delete:",
        reply_markup=_kb_cancel(), parse_mode=enums.ParseMode.HTML,
    )


@app.on_callback_query(filters.regex("^cfg_set_target$"))
async def cb_set_target(client: Client, cq: CallbackQuery):
    if not _is_authorized(cq.from_user.id):
        return await cq.answer("🚫 permission denied!", show_alert=True)
    await cq.answer()
    _awaiting[cq.from_user.id] = "set_target"
    current = await get_target_channel()
    await cq.message.edit_text(
        f"📡 <b>sєᴛ ᴛᴀʀɢєᴛ ᴄнᴀηηєʟ</b>\n\n"
        f"current: <code>{current or 'not set'}</code>\n\n"
        "send the channel id or @username\n"
        "<i>the channel you want to scrape waifus from.</i>",
        reply_markup=_kb_cancel(), parse_mode=enums.ParseMode.HTML,
    )


@app.on_callback_query(filters.regex("^cfg_fetch_all$"))
async def cb_fetch_all(client: Client, cq: CallbackQuery):
    if not _is_authorized(cq.from_user.id):
        return await cq.answer("🚫 permission denied!", show_alert=True)
    await cq.answer()

    target = await get_target_channel()
    count  = await get_waifu_count()

    if not target:
        return await cq.message.edit_text(
            "❌ <b>ᴛᴀʀɢєᴛ ᴄнᴀηηєʟ ηᴏᴛ sєᴛ!</b>\n"
            "go to config → set target channel first.",
            reply_markup=_kb_home(), parse_mode=enums.ParseMode.HTML,
        )

    await cq.message.edit_text(
        f"📥 <b>ғєᴛᴄн ᴀʟʟ ᴡᴀιғᴜs</b>\n\n"
        f"📡 <b>ᴛᴀʀɢєᴛ:</b>  <code>{target}</code>\n"
        f"🖼 <b>ᴄᴜʀʀєηᴛ ιη ᴅʙ:</b>  <code>{count}</code> waifus\n\n"
        "send <b>/wstart</b> to begin scraping.",
        reply_markup=_kb_home(), parse_mode=enums.ParseMode.HTML,
    )


@app.on_callback_query(filters.regex("^cfg_set_keymsg$"))
async def cb_set_keymsg(client: Client, cq: CallbackQuery):
    if not _is_authorized(cq.from_user.id):
        return await cq.answer("🚫 permission denied!", show_alert=True)
    await cq.answer()
    _awaiting[cq.from_user.id] = "set_keymsg"
    current = await get_keyboard_message()
    await cq.message.edit_text(
        f"💬 <b>sєᴛ ᴋєʏʙᴏᴀʀᴅ ϻєssᴀɢє</b>\n\n"
        f"current:\n<code>{current or 'not set'}</code>\n\n"
        "send the new message:",
        reply_markup=_kb_cancel(), parse_mode=enums.ParseMode.HTML,
    )


@app.on_callback_query(filters.regex("^cfg_toggle_autofetch$"))
async def cb_toggle_autofetch(client: Client, cq: CallbackQuery):
    if not _is_authorized(cq.from_user.id):
        return await cq.answer("🚫 permission denied!", show_alert=True)
    await cq.answer()
    current = await get_auto_fetch()
    new_val = not current
    await set_auto_fetch(new_val)
    status = "🟢 on" if new_val else "🔴 off"
    await cq.message.edit_text(
        f"🔄 <b>ᴀᴜᴛᴏ ғєᴛᴄн ηєᴡ ᴡᴀιғᴜs:</b>  {status}\n\n"
        "<i>new waifus will be captured automatically as they arrive.</i>",
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton("˹ 🔄 𝐓ᴏɢɢʟє ˼",  callback_data="cfg_toggle_autofetch"),
                InlineKeyboardButton("˹ ◀️ 𝐁ᴀᴄᴋ ˼",    callback_data="menu_config_p3"),
            ],
            [InlineKeyboardButton("˹ 𝚮ᴏϻє ˼",          callback_data="menu_home")],
        ]),
        parse_mode=enums.ParseMode.HTML,
    )
  
