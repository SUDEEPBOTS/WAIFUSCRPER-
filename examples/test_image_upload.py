# --------------------------------------------------------------------------
# Copyright (c) 2026 TOXICXD43 / SUDEEPBOTS. All Rights Reserved.
# Licensed under the MIT License. See LICENSE in the project root for details.
# --------------------------------------------------------------------------

"""
WAIFUSCRPER — Image Hoster Benchmark
Standalone tester for Catbox and ImgBB image uploads with latency measurements.
"""

import sys
import os
import time
import asyncio
import aiohttp

# Add root directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import config
from WAIFUSCRPER.tools.dwonloder.Dwonlod import upload_image

# 1x1 transparent PNG for lightweight API test
SAMPLE_IMAGE_BYTES = (
    b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06'
    b'\x00\x00\x00\x1f\x15c4\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01'
    b'\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82'
)

async def test_upload():
    print("=" * 60)
    print("🌸 WAIFUSCRPER — Image Upload Benchmark")
    print("=" * 60)
    print(f"CATBOX_HASH configured: {'YES' if config.CATBOX_HASH else 'NO (Anonymous)'}")
    print(f"IMGBB_KEY configured:   {'YES' if config.IMGBB_KEY else 'NO'}")

    print("\n⏳ Testing upload pipeline (Catbox -> ImgBB fallback)...")
    t0 = time.perf_counter()
    url = await upload_image(SAMPLE_IMAGE_BYTES, "test_waifu.png")
    elapsed = (time.perf_counter() - t0) * 1000

    if url:
        print(f"✅ Upload succeeded in {elapsed:.1f}ms!")
        print(f"🔗 Hosted URL: {url}")
    else:
        print(f"❌ Upload failed in {elapsed:.1f}ms. Check network or API keys.")

if __name__ == "__main__":
    asyncio.run(test_upload())
