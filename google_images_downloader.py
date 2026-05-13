import os
import sys
import zipfile
import json
from datetime import datetime
import requests
from duckduckgo_search import DDGS

def search_and_download_images(query, target_count, quality="high"):
    """
    جستجو و دانلود تصاویر از DuckDuckGo
    
    Args:
        query: عبارت جستجو
        target_count: تعداد تصاویر مورد نظر
        quality: کیفیت تصاویر (high/medium)
    """
    print(f"🔍 شروع جستجو در DuckDuckGo: {query}")
    print(f"🎯 تعداد هدف: {target_count} تصویر")
    
    # ایجاد پوشه دانلود
    download_dir = "downloads"
    os.makedirs(download_dir, exist_ok=True)
    
    # پوشه موقت با timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    images_folder = os.path.join(download_dir, f"temp_{timestamp}")
    os.makedirs(images_folder, exist_ok=True)
    
    downloaded_count = 0
    failed_count = 0
    all_results = []
    
    try:
        # استفاده از DDGS برای جستجو
        with DDGS() as ddgs:
            print("🔄 در حال جستجو...")
            
            # دریافت نتایج تصاویر
            results = ddgs.images(
                keywords=query,
                region="wt-wt",  # Worldwide
                safesearch="off",  # خاموش کردن فیلتر ایمن
                max_results=target_count,  # تعداد دقیق مورد نظر
                size="Wallpaper" if quality == "high" else None,  # کیفیت بالا
            )
            
            # تبدیل به لیست برای شمارش
            results_list = list(results)
            total_found = len(results_list)
            print(f"📸 {total_found} تصویر پیدا شد!")
            
            # دانلود تصاویر
            for idx, result in enumerate(results_list[:target_count]):
                try:
                    # دریافت لینک تصویر (کیفیت اصلی)
                    img_url = result.get('image')
                    if not img_url:
                        img_url = result.get('thumbnail')
                    
                    if img_url:
                        # تشخیص پسوند فایل
                        extension = img_url.split('.')[-1].split('?')[0].lower()
                        if extension not in ['jpg', 'jpeg', 'png', 'webp', 'gif']:
                            extension = 'jpg'
                        
                        filename = f"image_{idx+1:04d}.{extension}"
                        save_path = os.path.join(images_folder, filename)
                        
                        # دانلود تصویر
                        headers = {
                            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                        }
                        
                        response = requests.get(img_url, headers=headers, timeout=30, stream=True)
                        
                        if response.status_code == 200:
                            with open(save_path, 'wb') as f:
                                for chunk in response.iter_content(chunk_size=8192):
                                    f.write(chunk)
                            
                            downloaded_count += 1
                            print(f"✅ [{downloaded_count}/{target_count}] دانلود شد: {filename}")
                            
                            # ذخیره اطلاعات برای گزارش
                            all_results.append({
                                'index': idx + 1,
                                'url': img_url,
                                'title': result.get('title', ''),
                                'source': result.get('source', ''),
                                'filename': filename
                            })
                        else:
                            failed_count += 1
                            print(f"❌ دانلود ناموفق: HTTP {response.status_code}")
                    else:
                        failed_count += 1
                        print(f"⚠️ لینک معتبر یافت نشد برای تصویر {idx+1}")
                    
                    # تاخیر بین دانلودها
                    if idx < target_count - 1:
                        import time
                        time.sleep(0.5)
                        
                except Exception as e:
                    failed_count += 1
                    print(f"❌ خطا در دانلود تصویر {idx+1}: {e}")
            
    except Exception as e:
        print(f"💥 خطا در جستجو: {e}")
        return None, 0, 0
    
    # ایجاد فایل Zip
    if downloaded_count > 0:
        print(f"\n📦 ایجاد فایل Zip...")
        safe_query = "".join(c for c in query if c.isalnum() or c in "._- ")[:30]
        zip_name = f"{safe_query}_{downloaded_count}images_{timestamp}.zip"
        zip_path = os.path.join(download_dir, zip_name)
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(images_folder):
                for file in files:
                    if file.endswith(('.jpg', '.jpeg', '.png', '.webp', '.gif')):
                        file_path = os.path.join(root, file)
                        zipf.write(file_path, file)
        
        # حذف پوشه موقت
        import shutil
        shutil.rmtree(images_folder)
        
        # ذخیره گزارش JSON
        report_data = {
            'search_query': query,
            'target_count': target_count,
            'downloaded_count': downloaded_count,
            'failed_count': failed_count,
            'quality': quality,
            'date': datetime.now().isoformat(),
            'results': all_results
        }
        
        report_path = os.path.join(download_dir, f"report_{timestamp}.json")
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Zip ایجاد شد: {zip_path}")
        print(f"📊 گزارش ذخیره شد: {report_path}")
        
        return zip_path, downloaded_count, failed_count
    else:
        print("❌ هیچ تصویری دانلود نشد!")
        return None, 0, failed_count

def main():
    # دریافت پارامترها
    if len(sys.argv) < 3:
        print("Usage: python google_images_downloader.py <search_query> <num_images> [quality]")
        print("Example: python google_images_downloader.py 'cat' 50 high")
        sys.exit(1)
    
    search_query = sys.argv[1]
    target_count = int(sys.argv[2])
    quality = sys.argv[3] if len(sys.argv) > 3 else "high"
    
    # اجرای جستجو و دانلود
    zip_path, downloaded, failed = search_and_download_images(search_query, target_count, quality)
    
    # گزارش نهایی
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
