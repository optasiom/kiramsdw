import os
import sys
import time
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
import glob

def setup_driver():
    """راه‌اندازی مرورگر Chrome برای GitHub Actions"""
    chrome_options = Options()
    
    # تنظیمات ضروری برای GitHub Actions
    chrome_options.add_argument("--headless=new")  # حالت بدون رابط گرافیکی
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--disable-software-rasterizer")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    # مسیر کروم را مشخص کنید (برای اطمینان)
    chrome_options.binary_location = "/usr/bin/google-chrome"
    
    try:
        driver = webdriver.Chrome(options=chrome_options)
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        return driver
    except Exception as e:
        print(f"خطا در راه‌اندازی Chrome: {e}")
        # تلاش با مسیر جایگزین
        chrome_options.binary_location = "/usr/bin/google-chrome-stable"
        driver = webdriver.Chrome(options=chrome_options)
        return driver

def scroll_to_load_more(driver, target_count, current_count, max_attempts=50):
    """اسکرول کردن تا رسیدن به تعداد تصاویر مورد نظر"""
    attempts = 0
    last_height = driver.execute_script("return document.body.scrollHeight")
    
    while current_count < target_count and attempts < max_attempts:
        # اسکرول به پایین
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
        
        # بررسی دکمه "نمایش موارد بیشتر"
        try:
            show_more_selectors = [
                "//input[@value='Show more results']",
                "//span[contains(text(),'Show more results')]",
                "//button[contains(.,'Show more')]",
                "//div[contains(@role,'button') and contains(.,'Show more')]"
            ]
            
            for selector in show_more_selectors:
                try:
                    show_more = WebDriverWait(driver, 3).until(
                        EC.element_to_be_clickable((By.XPATH, selector))
                    )
                    driver.execute_script("arguments[0].scrollIntoView(true);", show_more)
                    time.sleep(1)
                    show_more.click()
                    print("✅ کلیک روی دکمه 'نمایش موارد بیشتر'")
                    time.sleep(2)
                    break
                except:
                    continue
        except:
            pass
        
        # شمارش مجدد تصاویر
        thumbnails = driver.find_elements(By.CSS_SELECTOR, "img.rg_i.Q4LuWd, img.YQ4gaf, img[jsname]")
        current_count = len(thumbnails)
        print(f"📸 تصاویر یافت شده: {current_count}/{target_count}")
        
        # بررسی توقف اسکرول
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            attempts += 1
            print(f"⚠️ ارتفاع صفحه تغییری نکرد، تلاش {attempts}/{max_attempts}")
        else:
            attempts = 0
            last_height = new_height
        
        time.sleep(1.5)
    
    return current_count

def get_high_res_url(driver, thumbnail, quality="high"):
    """دریافت لینک تصویر با کیفیت اصلی"""
    try:
        # اسکرول به سمت تصویر و کلیک
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", thumbnail)
        time.sleep(1)
        
        # کلیک با جاوااسکریپت برای اطمینان
        driver.execute_script("arguments[0].click();", thumbnail)
        time.sleep(2)
        
        # انتظار برای بارگذاری پنل
        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "img.n3VNCb, img.sFlh5c"))
        )
        
        # روش‌های مختلف برای یافتن لینک با کیفیت بالا
        url_methods = [
            # روش 1: تصویر اصلی در پنل
            lambda: driver.find_element(By.CSS_SELECTOR, "img.n3VNCb").get_attribute("src"),
            # روش 2: تصویر با کلاس sFlh5c
            lambda: driver.find_element(By.CSS_SELECTOR, "img.sFlh5c").get_attribute("src"),
            # روش 3: از طریق متادیتا
            lambda: driver.execute_script("""
                const img = document.querySelector('.v4dQwb img, .n3VNCb, .sFlh5c');
                return img ? img.src : null;
            """),
            # روش 4: لینک داخل anchor
            lambda: driver.execute_script("""
                const a = document.querySelector('.v4dQwb a, [jsname="sTFXNd"] a');
                return a ? a.href : null;
            """)
        ]
        
        for method in url_methods:
            try:
                url = method()
                if url and url.startswith("http") and not url.startswith("data:"):
                    if any(ext in url.lower() for ext in ['.jpg', '.jpeg', '.png', '.webp', '.gif']):
                        return url
                    elif "googleusercontent" in url:
                        return url
            except:
                continue
        
        return None
    except Exception as e:
        print(f"⚠️ خطا در دریافت لینک: {e}")
        return None

def download_image(url, save_path, timeout=20):
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
            if 'image' in content_type or url.endswith(('.jpg', '.jpeg', '.png', '.webp', '.gif')):
                with open(save_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                return True
            else:
                print(f"⚠️ نوع محتوا: {content_type}")
                return False
        else:
            return False
    except Exception as e:
        print(f"❌ خطا در دانلود: {e}")
        return False

def create_zip(folder_path, query):
    """ایجاد فایل Zip از تصاویر دانلود شده"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_query = "".join(c for c in query if c.isalnum() or c in "._- ")[:30]
    zip_name = f"{safe_query}_{timestamp}.zip"
    zip_path = os.path.join(folder_path, zip_name)
    
    # پیدا کردن همه فایل‌های تصویر
    image_files = []
    for ext in ['*.jpg', '*.jpeg', '*.png', '*.webp', '*.gif']:
        image_files.extend(glob.glob(os.path.join(folder_path, ext)))
    
    if not image_files:
        return None
    
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for img_file in image_files:
            zipf.write(img_file, os.path.basename(img_file))
    
    return zip_path

def main():
    # دریافت پارامترها
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
    images_folder = os.path.join(download_dir, f"temp_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
    os.makedirs(images_folder, exist_ok=True)
    
    driver = None
    try:
        print("🚀 راه‌اندازی مرورگر Chrome...")
        driver = setup_driver()
        
        # ساخت URL جستجو
        search_url = f"https://www.google.com/search?q={urllib.parse.quote(search_query)}&tbm=isch&hl=en&source=lnms"
        print(f"🌐 دسترسی به: {search_url}")
        driver.get(search_url)
        time.sleep(5)
        
        # بستن پنجره کوکی
        try:
            cookie_buttons = driver.find_elements(By.XPATH, "//button[contains(.,'Accept all') or contains(.,'Accept') or contains(.,'I agree')]")
            if cookie_buttons:
                cookie_buttons[0].click()
                time.sleep(2)
                print("✅ کوکی‌ها بسته شد")
        except:
            pass
        
        downloaded_count = 0
        failed_count = 0
        max_attempts_without_new = 10
        attempts_without_new = 0
        
        while downloaded_count < target_count and attempts_without_new < max_attempts_without_new:
            # پیدا کردن تصاویر
            thumbnails = driver.find_elements(By.CSS_SELECTOR, "img.rg_i.Q4LuWd, img.YQ4gaf, img[jsname]")
            available_count = len(thumbnails)
            print(f"\n📊 وضعیت: {downloaded_count} دانلود / {available_count} موجود / هدف {target_count}")
            
            if available_count == 0:
                print("❌ هیچ تصویری یافت نشد!")
                break
            
            # اسکرول برای دریافت تصاویر بیشتر
            if available_count < target_count:
                scroll_to_load_more(driver, target_count, available_count)
                continue
            
            # دانلود تصاویر جدید
            previous_downloaded = downloaded_count
            remaining = min(target_count - downloaded_count, available_count - downloaded_count)
            
            for i in range(downloaded_count, min(downloaded_count + remaining, available_count)):
                try:
                    thumb = thumbnails[i]
                    print(f"🖼️ پردازش تصویر {downloaded_count + 1}/{target_count}...")
                    
                    img_url = get_high_res_url(driver, thumb, quality)
                    
                    if img_url:
                        ext = img_url.split('.')[-1].split('?')[0][:4]
                        if ext.lower() not in ['jpg', 'jpeg', 'png', 'webp', 'gif']:
                            ext = 'jpg'
                        filename = f"image_{downloaded_count + 1:04d}.{ext}"
                        save_path = os.path.join(images_folder, filename)
                        
                        if download_image(img_url, save_path):
                            downloaded_count += 1
                            print(f"✅ دانلود شد: {filename}")
                        else:
                            failed_count += 1
                            print(f"❌ دانلود ناموفق")
                    else:
                        failed_count += 1
                        print(f"⚠️ لینک معتبر یافت نشد")
                    
                    time.sleep(1)
                    
                except Exception as e:
                    failed_count += 1
                    print(f"❌ خطا در پردازش: {e}")
            
            # بررسی پیشرفت
            if downloaded_count == previous_downloaded:
                attempts_without_new += 1
                print(f"⚠️ هیچ تصویر جدیدی دانلود نشد. تلاش {attempts_without_new}/{max_attempts_without_new}")
            else:
                attempts_without_new = 0
        
        # ایجاد فایل Zip
        if downloaded_count > 0:
            print(f"\n📦 ایجاد فایل Zip...")
            zip_path = create_zip(images_folder, search_query)
            if zip_path and os.path.exists(zip_path):
                print(f"✅ Zip ایجاد شد: {zip_path}")
                print(f"📊 آمار نهایی: {downloaded_count} تصویر دانلود شد, {failed_count} ناموفق")
            else:
                print("❌ خطا در ایجاد فایل Zip")
        else:
            print("❌ هیچ تصویری دانلود نشد!")
        
        # ذخیره گزارش
        report_path = os.path.join(download_dir, f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
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
