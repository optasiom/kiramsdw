import os
import sys
import zipfile
import json
import time
import re
from datetime import datetime
import requests

def search_duckduckgo_images(query, max_results=100):
    """جستجوی تصاویر در DuckDuckGo با استفاده از API عمومی"""
    
    # DuckDuckGo API endpoint
    url = "https://duckduckgo.com/"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Referer': 'https://duckduckgo.com/',
    }
    
    params = {
        'q': query,
        't': 'h_',
        'iax': 'images',
        'ia': 'images',
        'format': 'json'
    }
    
    try:
        response = requests.get(url + 'lite/', params=params, headers=headers)
        
        # روش دوم: استفاده از API vqd
        vqd_response = requests.post('https://duckduckgo.com/', data={'q': query}, headers=headers)
        vqd_match = re.search(r'vqd=([\d-]+)&', vqd_response.text)
        
        if vqd_match:
            vqd = vqd_match.group(1)
            
            images_url = "https://duckduckgo.com/i.js"
            images_params = {
                'q': query,
                'vqd': vqd,
                'iax': 'images',
                'ia': 'images',
                'p': '1',
                's': '0',
                'o': 'json'
            }
            
            all_images = []
            page = 0
            
            while len(all_images) < max_results:
                images_params['s'] = page * 100
                response = requests.get(images_url, params=images_params, headers=headers)
                
                if response.status_code == 200:
                    data = response.json()
                    results = data.get('results', [])
                    
                    if not results:
                        break
                    
                    for result in results:
                        image_url = result.get('image')
                        if image_url and image_url.startswith('http'):
                            all_images.append({
                                'image': image_url,
                                'thumbnail': result.get('thumbnail', ''),
                                'title': result.get('title', ''),
                                'source': result.get('source', '')
                            })
                    
                    if len(results) < 100:
                        break
                    
                    page += 1
                    time.sleep(0.5)
                else:
                    break
            
            return all_images[:max_results]
        
        return []
        
    except Exception as e:
        print(f"خطا در جستجو: {e}")
        return []

def download_image(url, save_path, timeout=30):
    """دانلود تصویر از URL"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=timeout, stream=True)
        
        if response.status_code == 200:
            # تشخیص نوع محتوا
            content_type = response.headers.get('content-type', '')
            if 'image' in content_type:
                # استخراج پسوند از URL یا content-type
                extension = 'jpg'
                if 'png' in content_type:
                    extension = 'png'
                elif 'webp' in content_type:
                    extension = 'webp'
                elif 'gif' in content_type:
                    extension = 'gif'
                elif 'jpeg' in content_type:
                    extension = 'jpeg'
                
                # یا از URL
                if '.' in url:
                    url_ext = url.split('.')[-1].split('?')[0].lower()
                    if url_ext in ['jpg', 'jpeg', 'png', 'webp', 'gif']:
                        extension = url_ext
                
                save_path = save_path.rsplit('.', 1)[0] + '.' + extension
                
                with open(save_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                return True, extension
            else:
                return False, None
        else:
            return False, None
    except Exception as e:
        print(f"خطا در دانلود: {e}")
        return False, None

def create_zip(folder_path, query, downloaded_count):
    """ایجاد فایل Zip"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_query = "".join(c for c in query if c.isalnum() or c in "._- ")[:30]
    zip_name = f"{safe_query}_{downloaded_count}images_{timestamp}.zip"
    zip_path = os.path.join(folder_path, zip_name)
    
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for file in os.listdir(folder_path):
            if file.startswith('img_') and file.endswith(('.jpg', '.jpeg', '.png', '.webp', '.gif')):
                file_path = os.path.join(folder_path, file)
                zipf.write(file_path, file)
    
    return zip_path

def search_and_download_images(query, target_count, quality="high"):
    """جستجو و دانلود تصاویر"""
    
    print(f"🔍 شروع جستجو در DuckDuckGo: {query}")
    print(f"🎯 تعداد هدف: {target_count} تصویر")
    
    # ایجاد پوشه دانلود
    download_dir = "downloads"
    os.makedirs(download_dir, exist_ok=True)
    
    # پوشه موقت
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    images_folder = os.path.join(download_dir, f"temp_{timestamp}")
    os.makedirs(images_folder, exist_ok=True)
    
    # جستجو
    print("🔄 در حال جستجو...")
    results = search_duckduckgo_images(query, target_count)
    
    if not results:
        print("❌ هیچ نتیجه‌ای پیدا نشد!")
        return None, 0, 0
    
    print(f"📸 {len(results)} تصویر پیدا شد!")
    
    # دانلود
    downloaded = 0
    failed = 0
    
    for idx, result in enumerate(results[:target_count]):
        img_url = result.get('image')
        
        if img_url:
            filename = f"img_{idx+1:04d}"
            temp_path = os.path.join(images_folder, filename)
            
            success, ext = download_image(img_url, temp_path)
            
            if success:
                # rename with correct extension
                final_path = os.path.join(images_folder, f"img_{idx+1:04d}.{ext}")
                os.rename(f"{temp_path}.{ext}", final_path)
                downloaded += 1
                print(f"✅ [{downloaded}/{target_count}] دانلود شد: img_{idx+1:04d}.{ext}")
            else:
                failed += 1
                print(f"❌ دانلود ناموفق: تصویر {idx+1}")
        else:
            failed += 1
            print(f"⚠️ لینک معتبر یافت نشد: تصویر {idx+1}")
        
        # تاخیر بین دانلودها
        if idx < target_count - 1:
            time.sleep(0.5)
    
    # ایجاد Zip
    if downloaded > 0:
        print(f"\n📦 ایجاد فایل Zip...")
        zip_path = create_zip(images_folder, query, downloaded)
        print(f"✅ Zip ایجاد شد: {zip_path}")
        
        # حذف پوشه موقت
        import shutil
        shutil.rmtree(images_folder)
        
        return zip_path, downloaded, failed
    else:
        print("❌ هیچ تصویری دانلود نشد!")
        return None, 0, failed

def main():
    if len(sys.argv) < 3:
        print("Usage: python google_images_downloader.py <search_query> <num_images> [quality]")
        sys.exit(1)
    
    search_query = sys.argv[1]
    target_count = int(sys.argv[2])
    quality = sys.argv[3] if len(sys.argv) > 3 else "high"
    
    zip_path, downloaded, failed = search_and_download_images(search_query, target_count, quality)
    
    print("\n" + "="*50)
    print("📊 گزارش نهایی:")
    print(f"✅ دانلود موفق: {downloaded}")
    print(f"❌ دانلود ناموفق: {failed}")
    if zip_path:
        print(f"📁 فایل خروجی: {zip_path}")
    print("="*50)
    
    if downloaded == 0:
        sys.exit(1)

if __name__ == "__main__":
    main()
