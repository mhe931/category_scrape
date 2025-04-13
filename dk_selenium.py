from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
from webdriver_manager.firefox import GeckoDriverManager
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import json
import time

BASE_URL = "https://www.digikala.com"

def setup_driver():
    options = Options()
    options.add_argument("--headless")
    
    try:
        driver = webdriver.Firefox(service=Service(GeckoDriverManager().install()), options=options)
        return driver
    except Exception as e:
        raise Exception("Could not initialize Firefox. Please ensure Firefox is installed. Error: " + str(e))

def get_main_categories(driver):
    driver.get(BASE_URL)
    time.sleep(2)
    categories = []

    try:
        cat_elements = driver.find_elements(By.CSS_SELECTOR, 'a.c-navi-new__main-link')
        for el in cat_elements:
            name = el.text.strip()
            href = el.get_attribute("href")
            if name and href:
                print(f"Main category: {name}")
                subcats = get_subcategories(driver, href, 1)
                categories.append({
                    "name": name,
                    "subcategories": subcats
                })
    except NoSuchElementException:
        print("Main categories not found.")
    return categories

def get_subcategories(driver, url, level, max_level=3):
    if level > max_level:
        return []

    subcategories = []
    driver.get(url)
    time.sleep(2)

    try:
        sub_elements = driver.find_elements(By.CSS_SELECTOR, 'a.c-product-box__title, a.c-listing__link')
        links_seen = set()
        for el in sub_elements:
            name = el.text.strip()
            href = el.get_attribute("href")
            if name and href and href not in links_seen:
                links_seen.add(href)
                print(f"{'--' * level} Subcategory: {name}")
                filters = get_filters(driver, href)
                deeper_subs = get_subcategories(driver, href, level + 1)
                subcategories.append({
                    "name": name,
                    "subcategories": deeper_subs,
                    "filters": filters
                })
            if len(subcategories) >= 5:
                break
    except Exception as e:
        print(f"Subcategory error at level {level}: {e}")

    return subcategories

def get_filters(driver, url):
    driver.get(url)
    time.sleep(2)
    filters = {}
    try:
        filter_sections = driver.find_elements(By.CSS_SELECTOR, '[data-testid="filter-section"]')
        for section in filter_sections:
            try:
                title_el = section.find_element(By.TAG_NAME, 'h4')
                title = title_el.text.strip()
                items = section.find_elements(By.CSS_SELECTOR, 'ul > li')
                values = [item.text.strip() for item in items if item.text.strip()]
                if values:
                    filters[title] = values
            except NoSuchElementException:
                continue
    except Exception as e:
        print(f"Filter extraction error: {e}")
    return filters

def main():
    driver = setup_driver()
    try:
        data = {
            "categories": get_main_categories(driver)
        }
        with open("digikala_categories_selenium.json", "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print("✅ JSON file saved successfully.")
    finally:
        driver.quit()

if __name__ == "__main__":
    main()



