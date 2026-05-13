# simple_pinterest_downloader.py
# بر اساس کد limkokhole اما ساده‌شده

import requests
import json
import time
import random
import os
from urllib.parse import quote

def download_pinterest_images(search_query, max_count=20):
    """دانلود تصاویر پینترست با جستجو"""
    
    # ایجاد پوشه
    os.makedirs("downloads", exist_ok=True)
    
    session = requests.Session()
    
    # هدرهای واقعی (مثل مرورگر)
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate, br',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    })
    
    # دریافت کوکی اولیه
    session.get('https://www.pinterest.com/')
    
    images = []
    bookmark = ""
    
    print(f"🔍 Searching for: {search_query}")
    
    while len(images) < max_count:
        # ساخت درخواست API
        data = {
            "options": {
                "query": search_query,
                "bookmarks": [bookmark] if bookmark else [],
                "page_size": min(25, max_count - len(images))
            }
        }
        
        params = {
            "source_url": f"/search/pins/?q={quote(search_query)}",
            "data": json.dumps(data)
        }
        
        try:
            time.sleep(random.uniform(2, 4))
            
            resp = session.get(
                "https://www.pinterest.com/resource/BaseSearchResource/get/",
                params=params,
                timeout=30
            )
            
            if resp.status_code != 200:
                print(f"❌ HTTP {resp.status_code}")
                break
            
            result = resp.json()
            pins = result.get("resource_response", {}).get("data", {}).get("results", [])
            
            if not pins:
                break
            
            for pin in pins:
                img_data = pin.get("images", {})
                img_url = None
                
                # اولویت کیفیت
                for quality in ["originals", "736x", "564x"]:
                    if quality in img_data:
                        img_url = img_data[quality].get("url")
                        if img_url:
                            break
                
                if img_url:
                    images.append({
                        "url": img_url,
                        "id": pin.get("id"),
                        "title": pin.get("title", f"image_{len(images)+1}")
                    })
                    print(f"📸 Found: {len(images)}/{max_count}")
                    
                    if len(images) >= max_count:
                        break
            
            bookmark = result.get("resource_response", {}).get("bookmark", "")
            if not bookmark:
                break
                
        except Exception as e:
            print(f"Error: {e}")
            break
    
    # دانلود تصاویر
    print(f"\n🚀 Downloading {len(images)} images...")
    
    downloaded = 0
    for idx, img in enumerate(images, 1):
        try:
            filename = f"downloads/{idx:03d}_{img['id']}.jpg"
            
            resp = session.get(img['url'], timeout=30)
            if resp.status_code == 200 and len(resp.content) > 5000:
                with open(filename, 'wb') as f:
                    f.write(resp.content)
                downloaded += 1
                print(f"✅ [{idx}] Downloaded ({len(resp.content)//1024}KB)")
            else:
                print(f"❌ [{idx}] Failed")
                
            time.sleep(1)
            
        except Exception as e:
            print(f"❌ [{idx}] Error: {e}")
    
    print(f"\n🎉 Complete! Downloaded {downloaded}/{len(images)} images")
    return downloaded

if __name__ == "__main__":
    # تغییر دهید
    SEARCH = "kagamine len"  # عبارت جستجو
    MAX_COUNT = 20           # تعداد عکس
    
    download_pinterest_images(SEARCH, MAX_COUNT)
