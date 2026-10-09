# --------------------------------------------------------------------------
# Copyright (c) 2026 TOXICXD43 / SUDEEPBOTS. All Rights Reserved.
# Licensed under the MIT License. See LICENSE in the project root for details.
# --------------------------------------------------------------------------

"""
WAIFUSCRPER — Export Waifus Utility
Exports MongoDB waifu collection into formatted JSON or CSV for backup or dataset training.
"""

import sys
import os
import json
import asyncio

# Add root directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import config
from WAIFUSCRPER.Database import get_collection, get_waifu_count

async def export_to_json(output_path: str = "waifus_export.json"):
    print("📦 Connecting to MongoDB...")
    col = await get_collection()
    count = await get_waifu_count()
    print(f"📊 Total Waifus in database: {count}")

    if count == 0:
        print("⚠️ Collection is empty. Nothing to export.")
        return

    print("⏳ Fetching records...")
    cursor = col.find({}, {"_id": 0})
    waifus = await cursor.to_list(length=None)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(waifus, f, indent=2, ensure_ascii=False)

    print(f"✅ Successfully exported {len(waifus)} waifus to: {output_path}")

if __name__ == "__main__":
    if not config.MONGO_URI:
        print("❌ Error: MONGO_URI not set in environment or .env file.")
        sys.exit(1)

    output_file = sys.argv[1] if len(sys.argv) > 1 else "waifus_export.json"
    asyncio.run(export_to_json(output_file))
