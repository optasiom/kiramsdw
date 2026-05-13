#!/usr/bin/env python3
"""
Pinterest Image Downloader - Optimized for GitHub Actions
نسخه بهینه شده برای اجرا در محیط GitHub Actions
"""

import json
import time
import random
import os
import asyncio
import aiohttp
import aiofiles
from typing import List, Dict, Optional
from datetime import datetime
from pathlib import Path
import requests
import sys

# ============ تنظیمات - قابل بازنویسی از محیط ============
class Config:
    # این مقادیر می‌توانند توسط GitHub Actions بازنویسی شوند
    SEARCH_QUERY = os.environ.get('PINTEREST_SEARCH', 'modern architecture')
    MAX_RESULTS = int(os.environ.get('PINTEREST_MAX_RESULTS', 50))
    IMAGE_QUALITY = os.environ.get('PINTEREST_QUALITY', '736x')  # 736x, originals, 564x
    
    # تاخیرها - در Actions ممکن است به مقادیر بیشتری نیاز باشد
    DELAY_BETWEEN_PAGES = (5, 8)  # افزایش برای جلوگیری از 429
    DELAY_BETWEEN_DOWNLOADS = (2, 4)
    
    # فایل‌ها - استفاده از مسیرهای نسبی
    URLS_FILE = "pinterest_urls.json"
    DOWNLOAD_DIR = "downloads"
    
    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
    ]

# [بقیه کلاس‌ها مانند قبل - PinterestURLExtractor و PinterestDownloader]
# (همان کدهایی که قبلاً نوشته بودیم با همین نام‌ها)

# ============ اجرای اصلی با هندلر خطای بهتر برای Actions ============
async def main():
    print("\n" + "="*50)
    print("🎨 Pinterest Downloader - GitHub Actions Mode")
    print("="*50)
    print(f"📝 Search: {Config.SEARCH_QUERY}")
    print(f"🎯 Max Results: {Config.MAX_RESULTS}")
    print(f"🖼️ Quality: {Config.IMAGE_QUALITY}")
    print(f"⏱️ Delay: {Config.DELAY_BETWEEN_PAGES[0]}-{Config.DELAY_BETWEEN_PAGES[1]}s")
    print(f"💻 Runner: {os.environ.get('RUNNER_OS', 'Unknown')}")
    print("="*50)
    
    try:
        # مرحله 1: استخراج لینک‌ها
        extractor = PinterestURLExtractor()
        urls_data = extractor.search_pins(Config.SEARCH_QUERY, Config.MAX_RESULTS)
        
        if not urls_data:
            print("❌ No URLs extracted!")
            sys.exit(1)
        
        extractor.save_urls(urls_data)
        
        # مرحله 2: دانلود
        downloader = PinterestDownloader()
        await downloader.download_all(Config.URLS_FILE)
        
        # نمایش آمار نهایی
        total_downloaded = len([f for f in Path(Config.DOWNLOAD_DIR).glob("*.jpg")])
        print(f"\n🎉 Success! Downloaded {total_downloaded} images to '{Config.DOWNLOAD_DIR}/'")
        
        # ایجاد فایل نشانگر موفقیت
        with open("success.txt", "w") as f:
            f.write(f"Download completed at {datetime.now().isoformat()}\n")
            f.write(f"Total images: {total_downloaded}\n")
        
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
