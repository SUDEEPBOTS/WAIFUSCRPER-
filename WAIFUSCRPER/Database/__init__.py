"""
WAIFUSCRPER — Database/__init__.py
Re-exports everything from MongoDB.py so rest of the project
can import cleanly:
    from WAIFUSCRPER.Database import waifu_exists, add_sudo, ...
"""

from WAIFUSCRPER.Database.MongoDB import (
    # ── Connection ───────────────────────────────
    get_collection,

    # ── Waifu ────────────────────────────────────
    waifu_exists,
    get_next_waifu_id,
    get_waifu_count,
    get_all_waifus,
    remove_waifu_by_id,
    drop_collection,

    # ── Sudo ─────────────────────────────────────
    add_sudo,
    remove_sudo,
    get_sudo_users,
    is_sudo,

    # ── Config ───────────────────────────────────
    set_logger,
    get_logger,
    remove_logger,

    set_target_channel,
    get_target_channel,
    remove_target_channel,

    set_collection_name,
    get_collection_name,
    remove_collection_name,

    set_approve_mode,
    get_approve_mode,

    set_auto_fetch,
    get_auto_fetch,

    set_string_session,
    get_string_session,
    remove_string_session,

    set_keyboard_message,
    get_keyboard_message,
)

__all__ = [
    "get_collection",
    "waifu_exists",
    "get_next_waifu_id",
    "get_waifu_count",
    "get_all_waifus",
    "remove_waifu_by_id",
    "drop_collection",
    "add_sudo",
    "remove_sudo",
    "get_sudo_users",
    "is_sudo",
    "set_logger",
    "get_logger",
    "remove_logger",
    "set_target_channel",
    "get_target_channel",
    "remove_target_channel",
    "set_collection_name",
    "get_collection_name",
    "remove_collection_name",
    "set_approve_mode",
    "get_approve_mode",
    "set_auto_fetch",
    "get_auto_fetch",
    "set_string_session",
    "get_string_session",
    "remove_string_session",
    "set_keyboard_message",
    "get_keyboard_message",
]

