import os
import sys
import zipfile
from datetime import datetime
from bing_image_downloader import downloader
import shutil
import time

def search_and_download_images(query, target_count, quality="high"):
    print(f"🔍 شروع جستجو در Bing: {query}")
    print(f"🎯 تعداد هدف: {target_count} تصویر")
    print(f"🔞 فیلتر محتوای بزرگسالانه: غیرفعال (adult_filter_off=True)")
    
    # ایجاد پوشه اصلی
    images_dir = "images"
    downloads_dir = "downloads"
    os.makedirs(images_dir, exist_ok=True)
    os.makedirs(downloads_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_query = "".join(c for c in query if c.isalnum() or c in "._- ")[:30]
    
    # پوشه نهایی برای ذخیره تصاویر
    final_folder = os.path.join(images_dir, f"{safe_query}_{timestamp}")
    os.makedirs(final_folder, exist_ok=True)
    
    all_downloaded_images = []
    batch_size = 25  # هر بار 25 تا دانلود کن (تعداد بهینه)
    current_batch = 0
    
    while len(all_downloaded_images) < target_count:
        current_batch += 1
        remaining = target_count - len(all_downloaded_images)
        current_limit = min(batch_size, remaining)
        
        print(f"\n🔄 مرحله {current_batch}: دانلود {current_limit} تصویر...")
        
        # پوشه موقت برای این مرحله
        temp_dir = f"temp_batch_{timestamp}_{current_batch}"
        
        try:
            # دانلود دسته جدید با adult_filter_off=True
            downloader.download(
                query,  # پارامتر موقعیتی
                limit=current_limit,
                output_dir=temp_dir,
                adult_filter_off=True,  # غیرفعال کردن فیلتر بزرگسالان
                force_replace=True,
                timeout=30,
                verbose=False  # برای لاگ کمتر
            )
            
            # پیدا کردن تصاویر دانلود شده
            download_path = os.path.join(temp_dir, query)
            if os.path.exists(download_path):
                new_images = [os.path.join(download_path, f) for f in os.listdir(download_path) 
                             if f.endswith(('.jpg', '.jpeg', '.png', '.webp', '.gif'))]
                
                # کپی به پوشه نهایی
                for idx, img_path in enumerate(new_images, len(all_downloaded_images) + 1):
                    ext = img_path.split('.')[-1]
                    new_filename = f"{safe_query}_{idx:04d}.{ext}"
                    new_path = os.path.join(final_folder, new_filename)
                    shutil.copy2(img_path, new_path)
                    all_downloaded_images.append(new_path)
                    print(f"   ✅ تصویر {idx} ذخیره شد")
            
            # پاک کردن پوشه موقت
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
            
            # صبر بین درخواست‌ها (برای جلوگیری از محدودیت)
            if len(all_downloaded_images) < target_count:
                time.sleep(3)
                
        except Exception as e:
            print(f"   ⚠️ خطا در مرحله {current_batch}: {e}")
            break
    
    downloaded_count = len(all_downloaded_images)
    print(f"\n✅ مجموعاً {downloaded_count} تصویر دانلود شد!")
    
    if downloaded_count == 0:
        return None, 0, 0
    
    # ایجاد فایل Zip
    zip_name = f"{safe_query}_{downloaded_count}images_{timestamp}.zip"
    zip_path = os.path.join(downloads_dir, zip_name)
    
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for img_path in all_downloaded_images:
            zipf.write(img_path, os.path.basename(img_path))
    
    # حذف فایل‌های تکراری از پوشه images؟ (اختیاری - اگر فقط میخواید zip بمونه)
    # shutil.rmtree(final_folder)
    
    print(f"\n✅ نتایج:")
    print(f"   📁 پوشه تصاویر: {final_folder}")
    print(f"   📦 فایل فشرده: {zip_path}")
    
    return zip_path, downloaded_count, 0

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
