from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
import os
import json
from urllib.request import Request, urlopen
import sys
import time

download_path = "dataset/"

def main():
    searchtext = sys.argv[1]
    num_requested = int(sys.argv[2])
    number_of_scrolls = num_requested // 400 + 1
    
    # ایجاد پوشه خروجی
    output_folder = download_path + searchtext.replace(" ", "_")
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    
    # تنظیمات Firefox برای حالت headless
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    
    # مسیر مستقیم به Firefox
    options.binary_location = "/usr/bin/firefox"
    
    # تنظیم Service برای geckodriver
    service = Service(executable_path="/usr/local/bin/geckodriver")
    
    print("🚀 در حال راه‌اندازی Firefox...")
    driver = webdriver.Firefox(options=options, service=service)
    
    url = f"https://www.google.com/search?q={searchtext}&source=lnms&tbm=isch"
    print(f"🌐 دسترسی به: {url}")
    driver.get(url)
    time.sleep(5)
    
    # بستن پنجره کوکی
    try:
        cookie_button = driver.find_element(By.XPATH, "//button[contains(.,'Accept all') or contains(.,'I agree')]")
        cookie_button.click()
        time.sleep(2)
        print("✅ کوکی‌ها بسته شد")
    except:
        pass
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    extensions = {"jpg", "jpeg", "png", "gif"}
    img_count = 0
    downloaded_img_count = 0
    
    # اسکرول و کلیک روی دکمه "نمایش موارد بیشتر"
    for scroll_num in range(number_of_scrolls):
        print(f"📜 اسکرول {scroll_num + 1}/{number_of_scrolls}...")
        for __ in range(10):
            driver.execute_script("window.scrollBy(0, 1000000)")
            time.sleep(0.2)
        time.sleep(1)
        try:
            show_more = driver.find_element(By.XPATH, "//input[@value='Show more results']")
            show_more.click()
            print("✅ کلیک روی دکمه 'نمایش موارد بیشتر'")
            time.sleep(2)
        except Exception as e:
            print(f"⚠️ دکمه بیشتری یافت نشد: {e}")
            break
    
    # پیدا کردن تصاویر
    images = driver.find_elements(By.XPATH, '//div[contains(@class,"rg_meta")]')
    print(f"\n📸 تعداد کل تصاویر پیدا شده: {len(images)}")
    
    for img in images:
        img_count += 1
        try:
            img_data = json.loads(img.get_attribute('innerHTML'))
            img_url = img_data.get("ou", "")
            img_type = img_data.get("ity", "jpg")
            
            if not img_url:
                continue
            
            if img_type not in extensions:
                img_type = "jpg"
            
            print(f"🖼️ دانلود تصویر {img_count}: {img_url[:80]}...")
            
            req = Request(img_url, headers=headers)
            raw_img = urlopen(req, timeout=30).read()
            
            filename = f"{downloaded_img_count}.{img_type}"
            filepath = os.path.join(output_folder, filename)
            
            with open(filepath, "wb") as f:
                f.write(raw_img)
            
            downloaded_img_count += 1
            print(f"✅ تصویر {downloaded_img_count} ذخیره شد: {filename}")
            
        except Exception as e:
            print(f"❌ خطا در دانلود تصویر {img_count}: {e}")
        
        if downloaded_img_count >= num_requested:
            break
    
    print(f"\n{'='*50}")
    print(f"📊 گزارش نهایی:")
    print(f"✅ دانلود موفق: {downloaded_img_count}")
    print(f"📸 کل تصاویر پردازش شده: {img_count}")
    print(f"{'='*50}")
    
    driver.quit()

if __name__ == "__main__":
    main()
