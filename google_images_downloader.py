import os
import sys
import zipfile
from datetime import datetime
from bing_image_downloader import downloader
import shutil

def search_and_download_images(query, target_count, quality="high"):
    """
    دانلود تصاویر از Bing با استفاده از کتابخانه به‌روز شده
    """
    print(f"🔍 شروع جستجو در Bing: {query}")
    print(f"🎯 تعداد هدف: {target_count} تصویر")
    print(f"⭐ کیفیت: {quality}")
    
    # تنظیم اندازه بر اساس کیفیت
    size_mapping = {
        "high": "wallpaper",
        "medium": "large"
    }
    selected_size = size_mapping.get(quality, "large")
    
    # ایجاد پوشه موقت
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    temp_dir = f"temp_download_{timestamp}"
    output_dir = "downloads"
    os.makedirs(output_dir, exist_ok=True)
    
    try:
        # استفاده از پارامتر صحیح query_string
        downloader.download(
            query_string=query,  # تغییر کلیدی اینجا است
            limit=target_count,
            output_dir=temp_dir,
            adult_filter_off=True,  # خاموش کردن فیلتر بزرگسالان
            force_replace=True,
            timeout=30,
            verbose=True,
            size=selected_size,  # تنظیم کیفیت تصاویر
            file_type='jpg,png,jpeg'  # فقط فرمت‌های استاندارد
        )
        
        # پیدا کردن تصاویر دانلود شده
        download_path = os.path.join(temp_dir, query)
        downloaded_images = []
        
        if os.path.exists(download_path):
            for file in os.listdir(download_path):
                if file.endswith(('.jpg', '.jpeg', '.png', '.webp', '.gif')):
                    downloaded_images.append(os.path.join(download_path, file))
        
        downloaded_count = len(downloaded_images)
        print(f"✅ {downloaded_count} تصویر دانلود شد!")
        
        if downloaded_count == 0:
            print("❌ هیچ تصویری دانلود نشد!")
            return None, 0, 0
        
        # ایجاد فایل Zip
        safe_query = "".join(c for c in query if c.isalnum() or c in "._- ")[:30]
        zip_name = f"{safe_query}_{downloaded_count}images_{timestamp}.zip"
        zip_path = os.path.join(output_dir, zip_name)
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for img_path in downloaded_images:
                zipf.write(img_path, os.path.basename(img_path))
        
        # پاک کردن فایل‌های موقت
        shutil.rmtree(temp_dir)
        
        print(f"✅ فایل Zip ایجاد شد: {zip_path}")
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
