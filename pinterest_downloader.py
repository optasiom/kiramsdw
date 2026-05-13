#!/usr/bin/env python3
"""
Pinterest Image Downloader - Optimized for GitHub Actions (Save to Repo)
نسخه ذخیره مستقیم در ریپازیتوری
"""

import json
import time
import random
import os
import asyncio
import aiohttp
import aiofiles
from typing import List, Dict
from datetime import datetime
from pathlib import Path
import requests

# ============ تنظیمات از محیط ============
class Config:
    SEARCH_QUERY = os.environ.get('PINTEREST_SEARCH', 'modern architecture')
    MAX_RESULTS = int(os.environ.get('PINTEREST_MAX_RESULTS', 50))
    IMAGE_QUALITY = os.environ.get('PINTEREST_QUALITY', '736x')
    
    DELAY_BETWEEN_PAGES = (4, 7)
    DELAY_BETWEEN_DOWNLOADS = (1.5, 3)
    
    URLS_FILE = "pinterest_urls.json"
    DOWNLOAD_DIR = "downloads"
    
    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
    ]

# ============ کلاس استخراج لینک ============
class PinterestURLExtractor:
    def __init__(self):
        self.session = requests.Session()
        self.csrf_token = None
        
    def _get_headers(self, is_api=False):
        headers = {
            "User-Agent": random.choice(Config.USER_AGENTS),
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": "https://www.pinterest.com/",
            "Origin": "https://www.pinterest.com",
        }
        if is_api and self.csrf_token:
            headers["X-CSRFToken"] = self.csrf_token
            headers["X-Requested-With"] = "XMLHttpRequest"
        return headers
    
    def _init_session(self):
        try:
            resp = self.session.get("https://www.pinterest.com/", headers=self._get_headers(), timeout=30)
            self.csrf_token = self.session.cookies.get("csrftoken", "")
            print(f"✅ Session initialized")
            return True
        except Exception as e:
            print(f"❌ Session error: {e}")
            return False
    
    def search_pins(self, query: str, max_results: int = 50) -> List[Dict]:
        if not self._init_session():
            return []
            
        collected_pins = []
        bookmark = ""
        page = 0
        
        print(f"\n🔍 Searching: '{query}' | Target: {max_results} images")
        
        while len(collected_pins) < max_results:
            page += 1
            
            data_payload = {
                "options": {
                    "query": query,
                    "scope": "pins",
                    "bookmarks": [bookmark] if bookmark else [],
                    "page_size": min(50, max_results - len(collected_pins))
                },
                "context": {}
            }
            
            params = {
                "source_url": f"/search/pins/?q={query}",
                "data": json.dumps(data_payload),
            }
            
            time.sleep(random.uniform(*Config.DELAY_BETWEEN_PAGES))
            
            try:
                resp = self.session.get(
                    "https://www.pinterest.com/resource/BaseSearchResource/get/",
                    headers=self._get_headers(is_api=True),
                    params=params,
                    timeout=30
                )
                
                if resp.status_code == 429:
                    print("⚠️ Rate limit! Waiting 60 seconds...")
                    time.sleep(60)
                    continue
                
                if resp.status_code != 200:
                    print(f"❌ HTTP {resp.status_code}")
                    break
                
                data = resp.json()
                results = data.get("resource_response", {}).get("data", {})
                pins_data = results.get("results", []) if isinstance(results, dict) else []
                
                if not pins_data:
                    print("🏁 End of results")
                    break
                
                new_count = 0
                for pin in pins_data:
                    images = pin.get("images", {})
                    
                    img_url = None
                    if Config.IMAGE_QUALITY in images:
                        img_url = images[Config.IMAGE_QUALITY].get("url")
                    
                    if not img_url:
                        for quality in ["736x", "564x", "474x"]:
                            if quality in images:
                                img_url = images[quality].get("url")
                                if img_url:
                                    break
                    
                    if img_url:
                        collected_pins.append({
                            "id": pin.get("id"),
                            "url": img_url,
                            "description": pin.get("description", "no_desc")[:50],
                        })
                        new_count += 1
                    
                    if len(collected_pins) >= max_results:
                        break
                
                print(f"📄 Page {page}: +{new_count} images | Total: {len(collected_pins)}/{max_results}")
                
                bookmark = data.get("resource_response", {}).get("bookmark", "")
                if not bookmark:
                    break
                    
            except Exception as e:
                print(f"❌ Error: {e}")
                break
        
        print(f"\n✅ Extraction complete: {len(collected_pins)} URLs")
        return collected_pins

# ============ کلاس دانلودر ============
class PinterestDownloader:
    def __init__(self):
        self.downloaded = 0
        self.failed = []
        
    async def download_image(self, session: aiohttp.ClientSession, pin: Dict, index: int) -> bool:
        url = pin.get("url")
        if not url:
            return False
        
        desc = pin.get("description", "no_desc")[:40].replace('/', '_').replace('\\', '_')
        filename = f"{index:04d}_{desc}.jpg"
        filepath = os.path.join(Config.DOWNLOAD_DIR, filename)
        
        await asyncio.sleep(random.uniform(*Config.DELAY_BETWEEN_DOWNLOADS))
        
        headers = {
            "User-Agent": random.choice(Config.USER_AGENTS),
            "Referer": "https://www.pinterest.com/",
        }
        
        try:
            async with session.get(url, headers=headers, timeout=30) as resp:
                if resp.status == 200:
                    content = await resp.read()
                    if len(content) > 5000:
                        async with aiofiles.open(filepath, 'wb') as f:
                            await f.write(content)
                        self.downloaded += 1
                        print(f"✅ [{index}] Downloaded: {filename}")
                        return True
                return False
        except Exception as e:
            print(f"❌ [{index}] Error: {str(e)[:50]}")
            return False
    
    async def download_all(self, urls_file: str):
        if not os.path.exists(urls_file):
            print(f"❌ File {urls_file} not found!")
            return
        
        with open(urls_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        urls_data = data.get("urls", [])
        total = len(urls_data)
        
        if total == 0:
            print("❌ No URLs found")
            return
        
        Path(Config.DOWNLOAD_DIR).mkdir(parents=True, exist_ok=True)
        
        print(f"\n🚀 Downloading {total} images to '{Config.DOWNLOAD_DIR}/'")
        
        connector = aiohttp.TCPConnector(limit=3)
        
        async with aiohttp.ClientSession(connector=connector) as session:
            tasks = []
            for idx, pin in enumerate(urls_data, 1):
                tasks.append(self.download_image(session, pin, idx))
            
            results = await asyncio.gather(*tasks)
            self.failed = [urls_data[i] for i, r in enumerate(results) if not r]
        
        print(f"\n✅ Downloaded: {self.downloaded}/{total}")

# ============ اجرای اصلی ============
async def main():
    print("\n" + "="*50)
    print("🎨 Pinterest Downloader - Save to Repository Mode")
    print("="*50)
    print(f"📝 Query: {Config.SEARCH_QUERY}")
    print(f"🎯 Count: {Config.MAX_RESULTS}")
    print(f"🖼️ Quality: {Config.IMAGE_QUALITY}")
    print("="*50)
    
    # استخراج لینک‌ها
    extractor = PinterestURLExtractor()
    urls_data = extractor.search_pins(Config.SEARCH_QUERY, Config.MAX_RESULTS)
    
    if not urls_data:
        print("❌ No URLs extracted!")
        return
    
    # ذخیره لینک‌ها
    with open(Config.URLS_FILE, 'w', encoding='utf-8') as f:
        json.dump({"urls": urls_data, "metadata": {"date": datetime.now().isoformat()}}, f, indent=2)
    
    # دانلود تصاویر
    downloader = PinterestDownloader()
    await downloader.download_all(Config.URLS_FILE)
    
    print(f"\n🎉 Success! Images saved in '{Config.DOWNLOAD_DIR}/'")

if __name__ == "__main__":
    asyncio.run(main())
