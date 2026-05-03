"""
WAIFUSCRPER — Dwonlod.py
Handles:
  • Image download from Telegram message
  • Upload to Catbox (primary) → ImgBB (fallback)
  • Caption parsing  (name / waifu_id / rarity / series / added_by)
  • Duplicate check
  • Save to MongoDB
"""

import re
import unicodedata
from datetime import datetime

import aiohttp
from loguru import logger

import config
from WAIFUSCRPER.Database import get_collection, waifu_exists, insert_waifu

# ── Upload Constants ───────────────────────────────────────────────────────────
CATBOX_URL  = "https://catbox.moe/user/api.php"
CATBOX_HASH = config.CATBOX_HASH          # in config.py
CATBOX_UA   = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 Chrome/124.0 Safari/537.36"
)
IMGBB_URL   = "https://api.imgbb.com/1/upload"
IMGBB_KEY   = config.IMGBB_KEY            # in config.py

TIMEOUT = aiohttp.ClientTimeout(total=30)


# ── Unicode Normalizer ─────────────────────────────────────────────────────────

def _normalize(text: str) -> str:
    """
    Convert bold/italic unicode letters (𝗥𝗮𝗿𝗶𝘁𝘆 → Rarity) to plain ASCII.
    Required because Telegram captions often use decorative unicode.
    """
    return unicodedata.normalize("NFKD", text)


# ── Image Upload ───────────────────────────────────────────────────────────────

async def _upload_catbox(data: bytes, filename: str) -> str | None:
    """Upload image bytes to catbox.moe. Returns URL or None."""
    try:
        form = aiohttp.FormData()
        form.add_field("reqtype",      "fileupload")
        form.add_field("userhash",     CATBOX_HASH)
        form.add_field(
            "fileToUpload", data,
            filename=filename,
            content_type="image/jpeg",
        )
        async with aiohttp.ClientSession(
            headers={"User-Agent": CATBOX_UA}
        ) as session:
            async with session.post(
                CATBOX_URL, data=form, timeout=TIMEOUT
            ) as resp:
                text = await resp.text()
                if resp.status == 200 and text.startswith("https://"):
                    return text.strip()
                logger.warning(f"Catbox bad response [{resp.status}]: {text[:80]}")
    except Exception as e:
        logger.warning(f"Catbox upload failed: {e}")
    return None


async def _upload_imgbb(data: bytes) -> str | None:
    """Upload image bytes to imgbb. Returns URL or None."""
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
                logger.warning(f"ImgBB error: {j}")
    except Exception as e:
        logger.warning(f"ImgBB upload failed: {e}")
    return None


async def upload_image(data: bytes, filename: str = "waifu.jpg") -> str | None:
    """
    Primary  → Catbox
    Fallback → ImgBB
    Returns hosted URL or None if both fail.
    """
    url = await _upload_catbox(data, filename)
    if not url:
        logger.info("Catbox failed → trying ImgBB…")
        url = await _upload_imgbb(data)
    if not url:
        logger.error("Both Catbox and ImgBB failed.")
    return url


# ── Photo Downloader ───────────────────────────────────────────────────────────

async def download_photo(client, msg) -> tuple[bytes, str] | tuple[None, None]:
    """
    Download the highest-quality photo from a Telegram message.
    Returns (image_bytes, filename) or (None, None) on failure.
    """
    try:
        buf = await client.download_media(msg.photo.file_id, in_memory=True)
        buf.seek(0)
        fname = f"waifu_{msg.id}.jpg"
        return buf.read(), fname
    except Exception as e:
        logger.error(f"Photo download error (msg_id={msg.id}): {e}")
        return None, None


# ── Caption Parser ─────────────────────────────────────────────────────────────

def parse_caption(caption: str) -> dict | None:
    """
    Parse a waifu channel caption.

    Expected format:
        UwU Check out this new character!

        <Series Name>
        <ID>: <Waifu Name>
        👒𝗥𝗮𝗿𝗶𝘁𝘆: 🎐 Celestial

        💉 𝑫𝒐𝒄𝒕𝒐𝒓 💉

        ᯓ➤ ᴀᴅᴅᴇᴅ ʙʏ: ༒GuN PaRK ♛

    Returns dict with keys:
        name, waifu_id, rarity, series, added_by
    or None if parsing fails.
    """
    if not caption:
        return None

    text = _normalize(caption)
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]

    result = {
        "name":      None,
        "waifu_id":  None,
        "rarity":    None,
        "series":    None,
        "added_by":  "Unknown",
    }

    for line in lines:
        # ── ID : Name  (e.g. "3793: Nobara Kugusaki") ─────────────────────────
        id_name = re.match(r"^(\d+)\s*:\s*(.+)$", line)
        if id_name:
            result["waifu_id"] = id_name.group(1).strip()
            result["name"]     = id_name.group(2).strip()
            continue

        # ── Rarity line  (e.g. "Rarity: 🎐 Celestial") ────────────────────────
        rarity_match = re.search(r"[Rr]arity\s*[:\-]\s*(.+)", line)
        if rarity_match:
            result["rarity"] = rarity_match.group(1).strip()
            continue

        # ── Added by line ──────────────────────────────────────────────────────
        added_match = re.search(
            r"(?:added\s+by|ᴀᴅᴅᴇᴅ\s+ʙʏ)\s*[:\-]\s*(.+)",
            line,
            re.IGNORECASE,
        )
        if added_match:
            result["added_by"] = added_match.group(1).strip()
            continue

    # ── Series: first non-special line that isn't name/id/rarity/added ────────
    skip_patterns = [
        r"^\d+\s*:",                                   # id:name line
        r"[Rr]arity",                                  # rarity line
        r"(?:added\s+by|ᴀᴅᴅᴇᴅ\s+ʙʏ)",               # added by
        r"^UwU",                                       # intro line
        r"^[💉🎐👒🌸✨🎴🎆]+",                       # emoji-only decorations
    ]
    for line in lines:
        is_skip = any(re.search(p, line, re.IGNORECASE) for p in skip_patterns)
        if not is_skip and result["series"] is None and not re.match(r"^\d+\s*:", line):
            result["series"] = line
            break

    # Must have at minimum name + waifu_id
    if not result["name"] or not result["waifu_id"]:
        logger.warning(f"Caption parse failed:\n{caption[:200]}")
        return None

    return result


# ── MongoDB Save ───────────────────────────────────────────────────────────────

async def save_waifu(parsed: dict, img_url: str, source_message_id: int) -> bool:
    """
    Save a parsed waifu document to MongoDB.
    Returns True on success, False if duplicate or error.
    """
    waifu_id = parsed["waifu_id"]

    # Duplicate check by waifu_id
    if await waifu_exists(waifu_id):
        logger.info(f"Duplicate skipped → waifu_id={waifu_id} ({parsed['name']})")
        return False

    doc = {
        "name":              parsed["name"],
        "img_url":           img_url,
        "rarity":            parsed.get("rarity", "Unknown"),
        "series":            parsed.get("series", "Unknown"),
        "event_tag":         "Standard",
        "source_message_id": source_message_id,
        "added_by":          parsed.get("added_by", "Unknown"),
        "id":                waifu_id,
        "waifu_id":          waifu_id,
        "Date":              datetime.utcnow().strftime("%d/%m/%Y"),
    }

    try:
        col = await get_collection()
        await col.insert_one(doc)
        logger.success(
            f"Saved ✅  [{waifu_id}] {parsed['name']} | {parsed.get('rarity')} | {img_url}"
        )
        return True
    except Exception as e:
        logger.error(f"MongoDB insert error: {e}")
        return False


# ── Main Processor ─────────────────────────────────────────────────────────────

async def process_waifu_message(client, msg) -> dict | None:
    """
    Full pipeline for one channel message:
      1. Parse caption
      2. Download photo
      3. Upload to Catbox / ImgBB
      4. Save to MongoDB

    Returns the saved waifu dict on success, None on any failure.
    Caller is responsible for approval flow (if APPROVE_MODE is on).
    """
    # ── Step 1: Parse caption ──────────────────────────────────────────────────
    caption = msg.caption or ""
    parsed  = parse_caption(caption)
    if not parsed:
        logger.warning(f"Skipping msg {msg.id} — caption parse failed")
        return None

    # ── Step 2: Download photo ─────────────────────────────────────────────────
    if not msg.photo:
        logger.warning(f"Skipping msg {msg.id} — no photo")
        return None

    data, fname = await download_photo(client, msg)
    if not data:
        return None

    # ── Step 3: Upload image ───────────────────────────────────────────────────
    img_url = await upload_image(data, fname)
    if not img_url:
        logger.error(f"Image upload failed for msg {msg.id}")
        return None

    # ── Step 4: Save ───────────────────────────────────────────────────────────
    saved = await save_waifu(parsed, img_url, source_message_id=msg.id)
    if not saved:
        return None  # duplicate or DB error

    return {**parsed, "img_url": img_url, "source_message_id": msg.id}
      
