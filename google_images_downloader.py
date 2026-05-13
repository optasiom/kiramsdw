import os
import sys
import zipfile
import json
from datetime import datetime
from bing_image_downloader import downloader
import shutil
import time

def search_and_download_images(query, target_count, quality="high"):
    """
    دانلود تصاویر از Bing با کیفیت بالا
    """
    print(f"🔍 شروع جستجو در Bing: {query}")
    print(f"🎯 تعداد هدف: {target_count} تصویر")
    print(f"⭐ کیفیت: {quality}")
    
    # تنظیم کیفیت
    size_filter = ""
    if quality == "high":
        size_filter = "large"  # تصاویر بزرگ
    elif quality == "medium":
        size_filter = "medium"  # تصاویر متوسط
    
    # ایجاد پوشه موقت
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    temp_dir = f"temp_download_{timestamp}"
    output_dir = "downloads"
    os.makedirs(output_dir, exist_ok=True)
    
    total_downloaded = 0
    failed = 0
    
    # برای دریافت تعداد بیشتر، جستجو را به چند بخش تقسیم می‌کنیم
    # با افزودن کلمات کلیدی مختلف به جستجو
    search_variations = [
        query,  # عبارت اصلی
        f"{query} art",  # با art
        f"{query} illustration",  # با illustration
        f"{query} wallpaper",  # با wallpaper
        f"{query} character",  # با character
        f"{query} drawing",  # با drawing
        f"{query} anime",  # با anime
        f"{query} 4k",  # با کیفیت 4k
    ]
    
    # محاسبه تعداد دانلود از هر منبع
    per_search_limit = max(10, target_count // len(search_variations))
    remaining = target_count
    
    for i, variant in enumerate(search_variations):
        if remaining <= 0:
            break
            
        print(f"\n🔄 جستجوی {i+1}/{len(search_variations)}: {variant}")
        current_limit = min(per_search_limit, remaining)
        
        try:
            # استفاده از نسخه کامل با فیلترهای بیشتر
            downloader.download(
                query=variant,
                limit=current_limit,
                output_dir=temp_dir,
                adult_filter_off=True,  # خاموش کردن فیلتر
                force_replace=False,
                timeout=30,
                verbose=True,
                filter="photo",  # فیلتر عکس
                size=size_filter if quality == "high" else None,
            )
            
            # پیدا کردن تصاویر دانلود شده
            download_path = os.path.join(temp_dir, variant)
            if os.path.exists(download_path):
                downloaded_images = [f for f in os.listdir(download_path) 
                                   if f.endswith(('.jpg', '.jpeg', '.png', '.webp', '.gif'))]
                
                new_downloads = len(downloaded_images)
                total_downloaded += new_downloads
                remaining -= new_downloads
                print(f"✅ از این جستجو {new_downloads} تصویر دانلود شد (مجموع: {total_downloaded})")
            else:
                print(f"⚠️ نتیجه‌ای برای '{variant}' پیدا نشد")
                failed += current_limit
                
        except Exception as e:
            print(f"❌ خطا در جستجوی '{variant}': {e}")
            failed += current_limit
        
        # تاخیر بین درخواست‌ها برای جلوگیری از محدودیت
        time.sleep(2)
    
    if total_downloaded == 0:
        print("❌ هیچ تصویری دانلود نشد!")
        return None, 0, 0
    
    # جمع‌آوری همه تصاویر در یک پوشه
    unified_folder = os.path.join(temp_dir, f"unified_{timestamp}")
    os.makedirs(unified_folder, exist_ok=True)
    
    image_counter = 1
    for root, dirs, files in os.walk(temp_dir):
        for file in files:
            if file.endswith(('.jpg', '.jpeg', '.png', '.webp', '.gif')):
                src_path = os.path.join(root, file)
                # حذف کاراکترهای غیرمجاز از اسم فایل
                safe_name = f"img_{image_counter:04d}.jpg"
                dst_path = os.path.join(unified_folder, safe_name)
                shutil.copy2(src_path, dst_path)
                image_counter += 1
    
    # ایجاد فایل Zip
    safe_query = "".join(c for c in query if c.isalnum() or c in "._- ")[:30]
    zip_name = f"{safe_query}_{total_downloaded}images_{timestamp}.zip"
    zip_path = os.path.join(output_dir, zip_name)
    
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(unified_folder):
            for file in files:
                file_path = os.path.join(root, file)
                zipf.write(file_path, file)
    
    # ذخیره گزارش
    report_data = {
        'search_query': query,
        'target_count': target_count,
        'downloaded_count': total_downloaded,
        'failed_count': failed,
        'quality': quality,
        'date': datetime.now().isoformat(),
        'source': 'Bing Images',
        'variations_used': search_variations
    }
    
    report_path = os.path.join(output_dir, f"report_{timestamp}.json")
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report_data, f, indent=2, ensure_ascii=False)
    
    # پاک کردن فایل‌های موقت
    shutil.rmtree(temp_dir)
    
    print(f"\n✅ فایل Zip ایجاد شد: {zip_path}")
    print(f"📊 مجموع: {total_downloaded} تصویر دانلود شد")
    
    return zip_path, total_downloaded, failed

def main():
    if len(sys.argv) < 3:
        print("Usage: python google_images_downloader.py <search_query> <num_images> [quality]")
        print("Example: python google_images_downloader.py 'cat' 50 high")
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
