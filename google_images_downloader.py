from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
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
    
    # تنظیمات Firefox برای حالت headless (بدون رابط گرافیکی)
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--window-size=1920,1080")
    
    url = f"https://www.google.com/search?q={searchtext}&source=lnms&tbm=isch"
    driver = webdriver.Firefox(options=options)
    driver.get(url)
    
    # بستن پنجره کوکی اگر ظاهر شد
    try:
        cookie_button = driver.find_element(By.XPATH, "//button[contains(.,'Accept all') or contains(.,'I agree')]")
        cookie_button.click()
        time.sleep(2)
    except:
        pass
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    extensions = {"jpg", "jpeg", "png", "gif"}
    img_count = 0
    downloaded_img_count = 0
    
    # اسکرول و کلیک روی دکمه "نمایش موارد بیشتر"
    for _ in range(number_of_scrolls):
        for __ in range(10):
            driver.execute_script("window.scrollBy(0, 1000000)")
            time.sleep(0.2)
        time.sleep(0.5)
        try:
            show_more = driver.find_element(By.XPATH, "//input[@value='Show more results']")
            show_more.click()
            time.sleep(2)
        except Exception as e:
            print(f"Less images found or no more button: {e}")
            break
    
    # پیدا کردن تصاویر
    images = driver.find_elements(By.XPATH, '//div[contains(@class,"rg_meta")]')
    print(f"Total images found: {len(images)}\n")
    
    for img in images:
        img_count += 1
        try:
            img_data = json.loads(img.get_attribute('innerHTML'))
            img_url = img_data.get("ou", "")
            img_type = img_data.get("ity", "jpg")
            
            if not img_url:
                continue
                
            print(f"Downloading image {img_count}: {img_url}")
            
            if img_type not in extensions:
                img_type = "jpg"
            
            req = Request(img_url, headers=headers)
            raw_img = urlopen(req, timeout=30).read()
            
            filename = f"{downloaded_img_count}.{img_type}"
            filepath = os.path.join(output_folder, filename)
            
            with open(filepath, "wb") as f:
                f.write(raw_img)
            
            downloaded_img_count += 1
            print(f"✅ Downloaded: {filename}")
            
        except Exception as e:
            print(f"Download failed for image {img_count}: {e}")
        
        if downloaded_img_count >= num_requested:
            break
    
    print(f"\n📊 Total downloaded: {downloaded_img_count}/{img_count}")
    driver.quit()

if __name__ == "__main__":
    main()
