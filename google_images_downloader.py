import os
import sys
import zipfile
import json
from datetime import datetime
from bing_image_downloader import downloader
import shutil

def search_and_download_images(query, target_count, quality="high"):
    """
    دانلود تصاویر از Bing
    """
    print(f"🔍 شروع جستجو در Bing: {query}")
    print(f"🎯 تعداد هدف: {target_count} تصویر")
    
    # ایجاد پوشه موقت
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    temp_dir = f"temp_download_{timestamp}"
    output_dir = "downloads"
    os.makedirs(output_dir, exist_ok=True)
    
    try:
        # دانلود با bing_image_downloader
        downloader.download(
            query=query,
            limit=target_count,
            output_dir=temp_dir,
            adult_filter_off=True,  # خاموش کردن فیلتر بزرگسالان
            force_replace=False,
            timeout=60,
            verbose=True
        )
        
        # پیدا کردن تصاویر دانلود شده
        downloaded_images = []
        download_path = os.path.join(temp_dir, query)
        
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
        
        # ذخیره گزارش
        report_data = {
            'search_query': query,
            'target_count': target_count,
            'downloaded_count': downloaded_count,
            'quality': quality,
            'date': datetime.now().isoformat(),
            'source': 'Bing Images'
        }
        
        report_path = os.path.join(output_dir, f"report_{timestamp}.json")
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)
        
        # پاک کردن فایل‌های موقت
        shutil.rmtree(temp_dir)
        
        print(f"✅ فایل Zip ایجاد شد: {zip_path}")
        return zip_path, downloaded_count, 0
        
    except Exception as e:
        print(f"💥 خطا: {e}")
        # پاک کردن فایل‌های موقت در صورت خطا
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
