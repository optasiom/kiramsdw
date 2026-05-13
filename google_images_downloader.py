import os
import sys
import time
import json
import zipfile
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, ElementClickInterceptedException
import urllib.parse
from datetime import datetime

def setup_driver():
    """راه‌اندازی مرورگر Chrome برای GitHub Actions"""
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")  # حالت بدون رابط گرافیکی
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    # برای GitHub Actions مسیر کروم مشخص می‌شود
    driver = webdriver.Chrome(options=chrome_options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    return driver

def scroll_to_load_more(driver, target_count, current_count, max_attempts=30):
    """اسکرول کردن تا رسیدن به تعداد تصاویر مورد نظر"""
    attempts = 0
    last_height = driver.execute_script("return document.body.scrollHeight")
    
    while current_count < target_count and attempts < max_attempts:
        # اسکرول به پایین
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(3)
        
        # بررسی دکمه "نمایش موارد بیشتر"
        try:
            show_more = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, "//input[@value='Show more results'] | //span[contains(text(),'نمایش موارد بیشتر')]"))
            )
            driver.execute_script("arguments[0].scrollIntoView(true);", show_more)
            time.sleep(1)
            show_more.click()
            print("✅ کلیک روی دکمه 'نمایش موارد بیشتر'")
            time.sleep(2)
        except:
            pass
        
        # شمارش مجدد تصاویر
        thumbnails = driver.find_elements(By.CSS_SELECTOR, "img.rg_i.Q4LuWd, img.YQ4gaf")
        current_count = len(thumbnails)
        print(f"📸 تصاویر یافت شده: {current_count}/{target_count}")
        
        # بررسی توقف اسکرول (اگر ارتفاع تغییر نکرد)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            attempts += 1
            print(f"⚠️ ارتفاع صفحه تغییری نکرد، تلاش {attempts}/{max_attempts}")
        else:
            attempts = 0
            last_height = new_height
        
        # تاخیر برای جلوگیری از محدودیت
        time.sleep(2)
    
    return current_count

def get_high_res_url(driver, thumbnail, quality="high"):
    """دریافت لینک تصویر با کیفیت اصلی"""
    try:
        # اسکرول به سمت تصویر و کلیک
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", thumbnail)
        time.sleep(1)
        driver.execute_script("arguments[0].click();", thumbnail)
        time.sleep(2)
        
        # روش‌های مختلف برای یافتن لینک با کیفیت بالا
        methods = [
            # روش 1: تصویر باز شده در پنل
            lambda: driver.find_element(By.CSS_SELECTOR, "img.sFlh5c.FyHeAf").get_attribute("src"),
            # روش 2: تصویر با کلاس n3VNCb
            lambda: driver.find_element(By.CSS_SELECTOR, "img.n3VNCb").get_attribute("src"),
            # روش 3: لینک داخل anchor
            lambda: driver.find_element(By.CSS_SELECTOR, "a[href^='http'] img").find_element(By.XPATH, "./ancestor::a").get_attribute("href"),
            # روش 4: از طریق متادیتا
            lambda: driver.execute_script("return document.querySelector('.v4dQwb')?.querySelector('a')?.href")
        ]
        
        for method in methods:
            try:
                url = method()
                if url and url.startswith("http") and not url.startswith("data:"):
                    # فیلتر کردن URLهای داده
                    if "googleusercontent" in url or ".jpg" in url or ".png" in url or ".jpeg" in url:
                        return url
            except:
                continue
        
        # روش آخر: گرفتن از background-image در صورت وجود
        try:
            style = thumbnail.get_attribute("style")
            if "url(" in style:
                url = style.split("url(")[1].split(")")[0].strip('"\'')
                if url.startswith("http"):
                    return url
        except:
            pass
        
        return None
    except Exception as e:
        print(f"⚠️ خطا در دریافت لینک: {e}")
        return None

def download_image(url, save_path, timeout=15):
    """دانلود تصویر از URL"""
    if not url:
        return False
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'image/webp,image/apng,image/*,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': 'https://www.google.com/'
        }
        
        response = requests.get(url, headers=headers, timeout=timeout, stream=True)
        
        if response.status_code == 200:
            content_type = response.headers.get('content-type', '')
            if 'image' in content_type:
                with open(save_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                return True
            else:
                print(f"❌ محتوا تصویر نیست: {content_type}")
                return False
        else:
            print(f"❌ خطا در دانلود: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ خطا در دانلود تصویر: {e}")
        return False

def create_zip(folder_path, query):
    """ایجاد فایل Zip از تصاویر دانلود شده"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_query = "".join(c for c in query if c.isalnum() or c in "._- ")[:30]
    zip_name = f"{safe_query}_{timestamp}.zip"
    zip_path = os.path.join(folder_path, zip_name)
    
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                if file.endswith(('.jpg', '.jpeg', '.png', '.webp', '.gif')):
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, folder_path)
                    zipf.write(file_path, arcname)
    
    return zip_path

def main():
    # دریافت پارامترها از آرگومان‌های خط فرمان
    if len(sys.argv) < 3:
        print("Usage: python google_images_downloader.py <search_query> <num_images> [quality]")
        sys.exit(1)
    
    search_query = sys.argv[1]
    target_count = int(sys.argv[2])
    quality = sys.argv[3] if len(sys.argv) > 3 else "high"
    
    print(f"🔍 شروع جستجو: {search_query}")
    print(f"🎯 تعداد هدف: {target_count} تصویر")
    print(f"⭐ کیفیت: {quality}")
    
    # ایجاد پوشه دانلود
    download_dir = "downloads"
    os.makedirs(download_dir, exist_ok=True)
    
    # پوشه موقت برای تصاویر
    images_folder = os.path.join(download_dir, f"temp_{search_query.replace(' ', '_')}")
    os.makedirs(images_folder, exist_ok=True)
    
    driver = None
    try:
        # راه‌اندازی مرورگر
        print("🚀 راه‌اندازی مرورگر...")
        driver = setup_driver()
        
        # ساخت URL جستجو
        search_url = f"https://www.google.com/search?q={urllib.parse.quote(search_query)}&tbm=isch&hl=en"
        print(f"🌐 دسترسی به: {search_url}")
        driver.get(search_url)
        time.sleep(5)
        
        # بستن پنجره کوکی اگر ظاهر شد
        try:
            cookie_button = driver.find_element(By.XPATH, "//button[contains(.,'Accept') or contains(.,'Accept all')]")
            cookie_button.click()
            time.sleep(2)
        except:
            pass
        
        # جمع‌آوری تصاویر تا رسیدن به تعداد مورد نظر
        downloaded_count = 0
        failed_count = 0
        
        while downloaded_count < target_count:
            # پیدا کردن تصاویر بندانگشتی
            thumbnails = driver.find_elements(By.CSS_SELECTOR, "img.rg_i.Q4LuWd, img.YQ4gaf")
            available_count = len(thumbnails)
            print(f"\n📊 وضعیت: {downloaded_count} دانلود شده / {available_count} موجود / هدف {target_count}")
            
            if available_count == 0:
                print("❌ هیچ تصویری یافت نشد!")
                break
            
            # اسکرول برای دریافت تصاویر بیشتر
            if available_count < target_count:
                scroll_to_load_more(driver, target_count, available_count)
                continue
            
            # پردازش تصاویر جدید
            remaining = target_count - downloaded_count
            to_process = min(remaining, available_count - downloaded_count)
            
            for i in range(downloaded_count, downloaded_count + to_process):
                try:
                    thumb = thumbnails[i]
                    print(f"🖼️ پردازش تصویر {downloaded_count + 1}/{target_count}...")
                    
                    # دریافت لینک با کیفیت
                    img_url = get_high_res_url(driver, thumb, quality)
                    
                    if img_url:
                        filename = f"img_{downloaded_count + 1:04d}.jpg"
                        save_path = os.path.join(images_folder, filename)
                        
                        if download_image(img_url, save_path):
                            downloaded_count += 1
                            print(f"✅ دانلود شد: {filename}")
                        else:
                            failed_count += 1
                            print(f"❌ دانلود ناموفق: تصویر {downloaded_count + 1}")
                    else:
                        failed_count += 1
                        print(f"⚠️ لینک معتبر یافت نشد: تصویر {downloaded_count + 1}")
                    
                    # تاخیر بین دانلودها
                    time.sleep(1)
                    
                except Exception as e:
                    failed_count += 1
                    print(f"❌ خطا در پردازش تصویر {downloaded_count + 1}: {e}")
        
        # ایجاد فایل Zip
        print(f"\n📦 ایجاد فایل Zip...")
        zip_path = create_zip(images_folder, search_query)
        print(f"✅ Zip ایجاد شد: {zip_path}")
        
        # حذف فایل‌های موقت
        import shutil
        shutil.rmtree(images_folder)
        
        # گزارش نهایی
        print("\n" + "="*50)
        print(f"📊 گزارش نهایی:")
        print(f"✅ دانلود موفق: {downloaded_count}")
        print(f"❌ دانلود ناموفق: {failed_count}")
        print(f"📁 فایل خروجی: {zip_path}")
        print("="*50)
        
        # ذخیره گزارش
        report_path = os.path.join(download_dir, f"report_{search_query}.txt")
        with open(report_path, 'w') as f:
            f.write(f"Search Query: {search_query}\n")
            f.write(f"Target Images: {target_count}\n")
            f.write(f"Successfully Downloaded: {downloaded_count}\n")
            f.write(f"Failed: {failed_count}\n")
            f.write(f"Quality: {quality}\n")
            f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
    except Exception as e:
        print(f"💥 خطای کلی: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
        
    finally:
        if driver:
            driver.quit()
            print("👋 مرورگر بسته شد")

if __name__ == "__main__":
    main()
