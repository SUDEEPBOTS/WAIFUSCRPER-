from pyrogram import enums

import re
import unicodedata
from datetime import datetime

import aiohttp
from loguru import logger

import config
from WAIFUSCRPER.Database import get_collection, waifu_exists, get_next_waifu_id

CATBOX_URL  = "https://catbox.moe/user/api.php"
CATBOX_HASH = config.CATBOX_HASH
CATBOX_UA   = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 Chrome/124.0 Safari/537.36"
)
IMGBB_URL = "https://api.imgbb.com/1/upload"
IMGBB_KEY = config.IMGBB_KEY

TIMEOUT = aiohttp.ClientTimeout(total=2)


def _normalize(text: str) -> str:
    """
    convert bold/italic unicode letters to plain ascii.
    required because telegram captions often use decorative unicode.
    """
    return unicodedata.normalize("NFKD", text)


async def _upload_catbox(data: bytes, filename: str) -> str | None:
    """upload image bytes to catbox.moe. returns url or none."""
    try:
        form = aiohttp.FormData()
        form.add_field("reqtype",  "fileupload")
        form.add_field("userhash", CATBOX_HASH)
        form.add_field(
            "fileToUpload", data,
            filename=filename,
            content_type="image/jpeg",
        )
        async with aiohttp.ClientSession(headers={"User-Agent": CATBOX_UA}) as session:
            async with session.post(CATBOX_URL, data=form, timeout=TIMEOUT) as resp:
                text = await resp.text()
                if resp.status == 200 and text.startswith("https://"):
                    return text.strip()
                logger.warning(f"catbox bad response [{resp.status}]: {text[:80]}")
    except Exception as e:
        logger.warning(f"catbox upload failed: {e}")
    return None


async def _upload_imgbb(data: bytes) -> str | None:
    """upload image bytes to imgbb. returns url or none."""
    try:
        import base64
        b64 = base64.b64encode(data).decode()
        async with aiohttp.ClientSession() as session:
            async with session.post(
                IMGBB_URL,
                data={"key": IMGBB_KEY, "image": b64},
                timeout=TIMEOUT,
            ) as resp:
                j = await resp.json()
                if j.get("success"):
                    return j["data"]["url"]
                logger.warning(f"imgbb error: {j}")
    except Exception as e:
        logger.warning(f"imgbb upload failed: {e}")
    return None


async def upload_image(data: bytes, filename: str = "waifu.jpg") -> str | None:
    """
    primary  -> catbox
    fallback -> imgbb
    returns hosted url or none if both fail.
    """
    url = await _upload_catbox(data, filename)
    if not url:
        logger.info("catbox failed, trying imgbb...")
        url = await _upload_imgbb(data)
    if not url:
        logger.error("both catbox and imgbb failed.")
    return url


async def download_photo(client, msg) -> tuple[bytes, str] | tuple[None, None]:
    """
    download the highest-quality photo from a telegram message.
    returns (image_bytes, filename) or (none, none) on failure.
    """
    try:
        buf = await client.download_media(msg.photo.file_id, in_memory=True)
        buf.seek(0)
        fname = f"waifu_{msg.id}.jpg"
        return buf.read(), fname
    except Exception as e:
        logger.error(f"photo download error (msg_id={msg.id}): {e}")
        return None, None


def parse_caption(caption: str) -> dict | None:
    """
    parse a waifu channel caption.

    expected format:
        uwu check out this new character!

        jujutsu kaisen
        3793: nobara kugusaki
        rarity: celestial

        added by: gun park

    returns dict:
        name       - waifu name (required)
        waifu_id   - str id or none (auto-generated in save_waifu if none)
        rarity     - rarity string or none
        series     - anime/series name or none
        added_by   - who added (default unknown)

    returns none only if name cannot be found.
    """
    if not caption:
        return None

    text  = _normalize(caption)
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]

    result = {
        "name":     None,
        "waifu_id": None,
        "rarity":   None,
        "series":   None,
        "added_by": "unknown",
    }

    for line in lines:
        id_name = re.match(r"^(\d+)\s*:\s*(.+)$", line)
        if id_name:
            result["waifu_id"] = id_name.group(1).strip()
            result["name"]     = id_name.group(2).strip()
            continue

        rarity_match = re.search(r"[Rr]arity\s*[:\-]\s*(.+)", line)
        if rarity_match:
            result["rarity"] = rarity_match.group(1).strip()
            continue

        added_match = re.search(
            r"(?:added\s+by|ᴀᴅᴅᴇᴅ\s+ʙʏ)\s*[:\-]\s*(.+)",
            line,
            re.IGNORECASE,
        )
        if added_match:
            result["added_by"] = added_match.group(1).strip()
            continue

    skip_patterns = [
        r"^\d+\s*:",
        r"[Rr]arity",
        r"(?:added\s+by|ᴀᴅᴅᴇᴅ\s+ʙʏ)",
        r"^UwU",
        r"^[💉🎐👒🌸✨🎴🎆]+",
    ]
    for line in lines:
        is_skip = any(re.search(p, line, re.IGNORECASE) for p in skip_patterns)
        if not is_skip and result["series"] is None and not re.match(r"^\d+\s*:", line):
            result["series"] = line
            break

    if not result["name"]:
        logger.warning(f"caption parse failed (no name found):\n{caption[:200]}")
        return None

    if not result["waifu_id"]:
        logger.info(f"no waifu_id in caption for '{result['name']}' — will auto-generate")

    return result


async def save_waifu(parsed: dict, img_url: str, source_message_id: int) -> bool:
    """
    save parsed waifu to mongodb.

    id logic:
      caption had id  -> use it directly
      caption had no id -> get last waifu_id from db and +1 (sequential)

    returns true on success, false if duplicate or db error.
    """
    waifu_id = parsed.get("waifu_id")

    if not waifu_id:
        waifu_id = str(await get_next_waifu_id())
        logger.info(f"auto-generated waifu_id={waifu_id} for '{parsed['name']}'")

    if await waifu_exists(waifu_id):
        logger.info(f"duplicate skipped -> waifu_id={waifu_id} ({parsed['name']})")
        return False

    doc = {
        "name":              parsed["name"],
        "img_url":           img_url,
        "rarity":            parsed.get("rarity") or "unknown",
        "series":            parsed.get("series") or "unknown",
        "event_tag":         "standard",
        "source_message_id": source_message_id,
        "added_by":          parsed.get("added_by") or "unknown",
        "id":                waifu_id,
        "waifu_id":          waifu_id,
        "Date":              datetime.utcnow().strftime("%d/%m/%Y"),
    }

    try:
        col = await get_collection()
        await col.insert_one(doc)
        logger.success(
            f"saved [{waifu_id}] {parsed['name']} | {parsed.get('rarity')} | {img_url}"
        )
        return True
    except Exception as e:
        logger.error(f"mongodb insert error: {e}")
        return False


async def process_waifu_message(client, msg) -> dict | None:
    """
    full pipeline for one channel message:
      1. parse caption
      2. download photo
      3. upload to catbox / imgbb
      4. save to mongodb

    returns saved waifu dict on success, none on any failure.
    approval flow is handled by the caller (auto.py).
    """
    caption = msg.caption or ""
    parsed  = parse_caption(caption)
    if not parsed:
        logger.warning(f"skipping msg {msg.id} — caption parse failed")
        return None

    if not msg.photo:
        logger.warning(f"skipping msg {msg.id} — no photo")
        return None

    data, fname = await download_photo(client, msg)
    if not data:
        return None

    img_url = await upload_image(data, fname)
    if not img_url:
        logger.error(f"image upload failed for msg {msg.id}")
        return None

    saved = await save_waifu(parsed, img_url, source_message_id=msg.id)
    if not saved:
        return None

    return {**parsed, "img_url": img_url, "source_message_id": msg.id}
  
