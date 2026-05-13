import os
import sys
import zipfile
import shutil
from datetime import datetime
from bing_image_downloader import downloader

def search_and_download_images(query, target_count, quality="high"):
    """
    دانلود تصاویر از Bing با نسخه جدید bing-image-downloader-ext
    که مشکل دانلود تعداد بالا رو حل کرده
    """
    print(f"🔍 شروع جستجو در Bing: {query}")
    print(f"🎯 تعداد هدف: {target_count} تصویر")
    print(f"⭐ کیفیت: {quality}")
    print(f"🔞 فیلتر محتوای بزرگسالانه: غیرفعال")

    # تنظیم کیفیت
    size_mapping = {
        "high": "wallpaper",   # بهترین کیفیت
        "medium": "large"      # کیفیت متوسط
    }
    selected_size = size_mapping.get(quality, "wallpaper")

    # ایجاد پوشه‌ها
    images_dir = "images"
    downloads_dir = "downloads"
    os.makedirs(images_dir, exist_ok=True)
    os.makedirs(downloads_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_query = "".join(c for c in query if c.isalnum() or c in "._- ")[:30]
    
    # پوشه موقت
    temp_dir = f"temp_download_{timestamp}"
    
    try:
        # دانلود با نسخه جدید (حالا limit تا 100 یا بیشتر رو پشتیبانی می‌کنه)
        downloader.download(
            query,
            limit=target_count,              # حالا می‌تونه تعداد بالا دانلود کنه!
            output_dir=temp_dir,
            adult_filter_off=True,           # غیرفعال کردن فیلتر بزرگسالان
            force_replace=True,
            timeout=30,
            verbose=True,
            size=selected_size,              # کیفیت بالا
            file_type='jpg,jpeg,png,webp'    # فرمت‌های قابل قبول
        )
        
        # پیدا کردن تصاویر دانلود شده
        download_path = os.path.join(temp_dir, query)
        downloaded_images = []

        if os.path.exists(download_path):
            for file in os.listdir(download_path):
                if file.endswith(('.jpg', '.jpeg', '.png', '.webp')):
                    downloaded_images.append(os.path.join(download_path, file))

        downloaded_count = len(downloaded_images)
        print(f"\n✅ {downloaded_count} تصویر دانلود شد!")

        if downloaded_count == 0:
            print("❌ هیچ تصویری دانلود نشد!")
            return None, 0, 0

        # ذخیره در پوشه نهایی
        final_folder = os.path.join(images_dir, f"{safe_query}_{timestamp}")
        os.makedirs(final_folder, exist_ok=True)

        for idx, img_path in enumerate(downloaded_images, 1):
            ext = img_path.split('.')[-1]
            new_filename = f"{safe_query}_{idx:04d}.{ext}"
            new_path = os.path.join(final_folder, new_filename)
            shutil.copy2(img_path, new_path)
            print(f"📁 ذخیره شد: {new_filename}")

        # ایجاد فایل Zip
        zip_name = f"{safe_query}_{downloaded_count}images_{timestamp}.zip"
        zip_path = os.path.join(downloads_dir, zip_name)

        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for img_path in downloaded_images:
                zipf.write(img_path, os.path.basename(img_path))

        # پاک کردن فایل‌های موقت
        shutil.rmtree(temp_dir)

        print(f"\n✅ تصاویر در مسیر زیر ذخیره شدند:")
        print(f"   📁 پوشه تصاویر: {final_folder}")
        print(f"   📦 فایل فشرده: {zip_path}")

        return zip_path, downloaded_count, 0

    except Exception as e:
        print(f"💥 خطا: {e}")
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
        return None, 0, 0

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
