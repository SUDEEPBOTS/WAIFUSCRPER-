"""
WAIFUSCRPER — Database/MongoDB.py
All MongoDB operations:
  • Connection & collection getter
  • Waifu CRUD
  • Sudo management
  • Bot config (logger, target channel, approve mode, etc.)
"""

from motor.motor_asyncio import AsyncIOMotorClient
from loguru import logger

import config

# ── Connection ─────────────────────────────────────────────────────────────────

_client: AsyncIOMotorClient | None = None


def _get_client() -> AsyncIOMotorClient:
    global _client
    if _client is None:
        _client = AsyncIOMotorClient(config.MONGO_URI)
        logger.info("ᴍᴏɴɢᴏᴅʙ ᴄᴏɴɴᴇᴄᴛᴇᴅ ✅")
    return _client


def _db():
    return _get_client()[config.DB_NAME]


# ── Collections ────────────────────────────────────────────────────────────────

async def get_collection():
    """
    Returns the active waifu collection.
    Collection name is fetched from bot_config (set via Telegram config).
    Falls back to 'waifus' if not set.
    """
    name = await get_collection_name() or "waifus"
    return _db()[name]


def _config_col():
    """Internal: bot config collection (stores all settings)."""
    return _db()["bot_config"]


def _sudo_col():
    """Internal: sudo users collection."""
    return _db()["sudo_users"]


# ══════════════════════════════════════════════════════════════════════════════
#  WAIFU FUNCTIONS
# ══════════════════════════════════════════════════════════════════════════════

async def waifu_exists(waifu_id: str) -> bool:
    """Check if a waifu with given waifu_id already exists in DB."""
    col = await get_collection()
    doc = await col.find_one({"waifu_id": str(waifu_id)})
    return doc is not None


async def get_next_waifu_id() -> int:
    """
    Sequential ID generator.
    Finds the highest numeric waifu_id in DB and returns +1.
    Starts from 1 if DB is empty.
    """
    col = await get_collection()
    cursor = col.find(
        {"waifu_id": {"$regex": r"^\d+$"}},
        {"waifu_id": 1}
    ).sort("waifu_id", -1).limit(1)

    async for doc in cursor:
        try:
            return int(doc["waifu_id"]) + 1
        except (ValueError, KeyError):
            pass

    return 1  # Empty DB — start from 1


async def get_waifu_count() -> int:
    """Total number of waifus in active collection."""
    col = await get_collection()
    return await col.count_documents({})


async def get_all_waifus(limit: int = 0) -> list[dict]:
    """Fetch all waifus. Pass limit=N to cap results."""
    col    = await get_collection()
    cursor = col.find({}, {"_id": 0})
    if limit:
        cursor = cursor.limit(limit)
    return await cursor.to_list(length=None)


async def remove_waifu_by_id(waifu_id: str) -> bool:
    """
    Delete a waifu by waifu_id.
    Returns True if deleted, False if not found.
    """
    col    = await get_collection()
    result = await col.delete_one({"waifu_id": str(waifu_id)})
    return result.deleted_count > 0


async def drop_collection() -> bool:
    """
    Drop (delete) the entire active waifu collection.
    Returns True on success.
    """
    try:
        col = await get_collection()
        await col.drop()
        logger.warning("ᴡᴀɪꜰᴜ ᴄᴏʟʟᴇᴄᴛɪᴏɴ ᴅʀᴏᴘᴘᴇᴅ!")
        return True
    except Exception as e:
        logger.error(f"Drop collection error: {e}")
        return False


# ══════════════════════════════════════════════════════════════════════════════
#  REJECTED WAIFU FUNCTIONS
# ══════════════════════════════════════════════════════════════════════════════

async def add_rejected_waifu(waifu_id: str) -> None:
    """rejected waifu ka id save karo taaki dubara na aaye."""
    col = _db()["rejected_waifus"]
    await col.update_one(
        {"waifu_id": str(waifu_id)},
        {"$set": {"waifu_id": str(waifu_id)}},
        upsert=True,
    )


async def is_rejected_waifu(waifu_id: str) -> bool:
    """check karo ki ye waifu pehle reject hua hai ya nahi."""
    col = _db()["rejected_waifus"]
    doc = await col.find_one({"waifu_id": str(waifu_id)})
    return doc is not None


# ══════════════════════════════════════════════════════════════════════════════
#  SUDO FUNCTIONS
# ══════════════════════════════════════════════════════════════════════════════

async def add_sudo(user_id: int) -> None:
    """Add a user to sudo list."""
    await _sudo_col().update_one(
        {"user_id": user_id},
        {"$set": {"user_id": user_id}},
        upsert=True,
    )


async def remove_sudo(user_id: int) -> None:
    """Remove a user from sudo list."""
    await _sudo_col().delete_one({"user_id": user_id})


async def get_sudo_users() -> list[int]:
    """Return list of all sudo user IDs."""
    cursor = _sudo_col().find({}, {"user_id": 1, "_id": 0})
    docs   = await cursor.to_list(length=None)
    return [d["user_id"] for d in docs]


async def is_sudo(user_id: int) -> bool:
    """Check if a user is sudo or owner."""
    if user_id == config.OWNER_ID:
        return True
    doc = await _sudo_col().find_one({"user_id": user_id})
    return doc is not None


# ══════════════════════════════════════════════════════════════════════════════
#  BOT CONFIG FUNCTIONS
#  All settings stored as key-value docs in 'bot_config' collection.
# ══════════════════════════════════════════════════════════════════════════════

async def _set_config(key: str, value) -> None:
    await _config_col().update_one(
        {"key": key},
        {"$set": {"key": key, "value": value}},
        upsert=True,
    )


async def _get_config(key: str, default=None):
    doc = await _config_col().find_one({"key": key})
    return doc["value"] if doc else default


async def _del_config(key: str) -> None:
    await _config_col().delete_one({"key": key})


# ── Logger ─────────────────────────────────────────────────────────────────────

async def set_logger(chat_id: int) -> None:
    await _set_config("logger_id", chat_id)

async def get_logger() -> int | None:
    return await _get_config("logger_id")

async def remove_logger() -> None:
    await _del_config("logger_id")


# ── Target Channel ─────────────────────────────────────────────────────────────

async def set_target_channel(chat_id: int) -> None:
    await _set_config("target_channel", chat_id)

async def get_target_channel() -> int | None:
    return await _get_config("target_channel")

async def remove_target_channel() -> None:
    await _del_config("target_channel")


# ── Collection Name ────────────────────────────────────────────────────────────

async def set_collection_name(name: str) -> None:
    await _set_config("collection_name", name)

async def get_collection_name() -> str | None:
    return await _get_config("collection_name")

async def remove_collection_name() -> None:
    await _del_config("collection_name")


# ── Approve Mode ───────────────────────────────────────────────────────────────

async def set_approve_mode(enabled: bool) -> None:
    await _set_config("approve_mode", enabled)

async def get_approve_mode() -> bool:
    return await _get_config("approve_mode", default=False)


# ── Auto Fetch New Waifus ──────────────────────────────────────────────────────

async def set_auto_fetch(enabled: bool) -> None:
    await _set_config("auto_fetch", enabled)

async def get_auto_fetch() -> bool:
    return await _get_config("auto_fetch", default=False)


# ── String Session ─────────────────────────────────────────────────────────────

async def set_string_session(session: str) -> None:
    await _set_config("string_session", session)

async def get_string_session() -> str | None:
    return await _get_config("string_session")

async def remove_string_session() -> None:
    await _del_config("string_session")


# ── Keyboard / Caption Message ─────────────────────────────────────────────────

async def set_keyboard_message(text: str) -> None:
    await _set_config("keyboard_message", text)

async def get_keyboard_message() -> str | None:
    return await _get_config("keyboard_message")
  
