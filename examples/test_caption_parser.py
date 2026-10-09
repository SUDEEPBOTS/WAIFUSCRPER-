# --------------------------------------------------------------------------
# Copyright (c) 2026 TOXICXD43 / SUDEEPBOTS. All Rights Reserved.
# Licensed under the MIT License. See LICENSE in the project root for details.
# --------------------------------------------------------------------------

"""
WAIFUSCRPER — Caption Parser Benchmark & Validator
Tests the regex normalization and caption parsing logic against diverse Telegram post formats.
"""

import re
import json
import unicodedata

SAMPLE_CAPTIONS = [
    """
    🌸 UwU check out this new character!

    Jujutsu Kaisen
    3793: Nobara Kugisaki
    Rarity: Celestial

    Added by: Gun Park
    """,
    """
    ✨ A rare gem appeared in the collection!

    Demon Slayer: Kimetsu no Yaiba
    1042: Nezuko Kamado
    Rarity: Mythic

    ᴀᴅᴅᴇᴅ ʙʏ: Tanjiro
    """,
    """
    👒 Solo Leveling
    582: Cha Hae-In
    Rarity - Legendary
    """,
    """
    Genshin Impact
    Raiden Shogun
    Rarity: Limited Edition
    """
]

def normalize(text: str) -> str:
    return unicodedata.normalize("NFKD", text)

def parse_caption(caption: str) -> dict | None:
    if not caption:
        return None

    text = normalize(caption)
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]

    result = {
        "name": None,
        "waifu_id": None,
        "rarity": None,
        "series": None,
        "added_by": "unknown",
    }

    for line in lines:
        id_name = re.match(r"^(\d+)\s*:\s*(.+)$", line)
        if id_name:
            result["waifu_id"] = id_name.group(1).strip()
            result["name"] = id_name.group(2).strip()
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

    # Fallback name search if not in "123: Name" format
    if not result["name"]:
        for line in lines:
            if not any(re.search(p, line, re.IGNORECASE) for p in skip_patterns) and line != result["series"]:
                result["name"] = line
                break

    return result

def main():
    print("=" * 60)
    print("🌸 WAIFUSCRPER — Caption Parser Test Suite")
    print("=" * 60)

    for i, cap in enumerate(SAMPLE_CAPTIONS, 1):
        print(f"\n[Test Case #{i}]")
        parsed = parse_caption(cap)
        print("Input Caption Preview:")
        print("  " + cap.strip().replace("\n", "\n  "))
        print("\nParsed Result:")
        print(json.dumps(parsed, indent=2))
        print("-" * 50)

if __name__ == "__main__":
    main()
