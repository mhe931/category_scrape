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
    time.sleep(5)  # Increased wait time
    categories = []

    try:
        # Try multiple possible selectors for main categories
        selectors = [
            'a.c-navi-new__main-link',
            'div.c-navi-new-list__category-link',
            'a[data-cro-id*="navigation"]',
            '.c-navi-new-list__inner-categories a'
        ]
        
        cat_elements = []
        for selector in selectors:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    cat_elements = elements
                    print(f"Found categories using selector: {selector}")
                    break
            except:
                continue

        if not cat_elements:
            print("No categories found with any selector")
            return categories

        for el in cat_elements:
            try:
                name = el.text.strip()
                href = el.get_attribute("href")
                if name and href and "digikala.com" in href:
                    print(f"Main category: {name} -> {href}")
                    subcats = get_subcategories(driver, href, 1)
                    categories.append({
                        "name": name,
                        "url": href,
                        "subcategories": subcats
                    })
            except Exception as e:
                print(f"Error processing category element: {e}")
                continue
                
    except Exception as e:
        print(f"Error in get_main_categories: {e}")
    
    print(f"Found {len(categories)} main categories")
    return categories

def get_subcategories(driver, url, level, max_level=3):
    if level > max_level:
        return []

    subcategories = []
    try:
        driver.get(url)
        time.sleep(5)  # Increased wait time

        # Try multiple selectors for subcategories
        selectors = [
            'a.c-product-box__title',
            'a.c-listing__link',
            'div.c-catalog__list a',
            '.c-navi-new-list__sublist-option a',
            '.c-navi-new-list__inner-categories a'
        ]
        
        sub_elements = []
        for selector in selectors:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    sub_elements.extend(elements)
            except:
                continue

        links_seen = set()
        for el in sub_elements:
            try:
                name = el.text.strip()
                href = el.get_attribute("href")
                if name and href and href not in links_seen and "digikala.com" in href:
                    links_seen.add(href)
                    print(f"{'--' * level} Subcategory: {name} -> {href}")
                    
                    filters = get_filters(driver, href)
                    deeper_subs = get_subcategories(driver, href, level + 1)
                    
                    subcategories.append({
                        "name": name,
                        "url": href,
                        "subcategories": deeper_subs,
                        "filters": filters
                    })
                
                if len(subcategories) >= 5:  # Limit subcategories per level
                    break
            except Exception as e:
                print(f"Error processing subcategory element: {e}")
                continue

    except Exception as e:
        print(f"Error in get_subcategories at level {level}: {e}")

    print(f"Found {len(subcategories)} subcategories at level {level}")
    return subcategories

def get_filters(driver, url):
    try:
        driver.get(url)
        time.sleep(3)  # Increased wait time
        filters = {}

        # Try multiple selectors for filter sections
        filter_selectors = [
            '[data-testid="filter-section"]',
            '.c-filter__items',
            '.c-box__filters'
        ]

        for selector in filter_selectors:
            try:
                filter_sections = driver.find_elements(By.CSS_SELECTOR, selector)
                if filter_sections:
                    for section in filter_sections:
                        try:
                            # Try different ways to get the title
                            title_el = None
                            for title_tag in ['h4', 'h3', 'div.filter-title']:
                                try:
                                    title_el = section.find_element(By.CSS_SELECTOR, title_tag)
                                    break
                                except:
                                    continue
                            
                            if title_el:
                                title = title_el.text.strip()
                                # Try different selectors for filter items
                                items = []
                                for item_selector in ['ul > li', '.c-filter__item', '.c-filter__label']:
                                    try:
                                        items = section.find_elements(By.CSS_SELECTOR, item_selector)
                                        if items:
                                            break
                                    except:
                                        continue

                                values = [item.text.strip() for item in items if item.text.strip()]
                                if values:
                                    filters[title] = values
                        except Exception as e:
                            print(f"Error processing filter section: {e}")
                            continue
                    
                    if filters:  # If we found filters with this selector, stop trying others
                        break
            except Exception as e:
                print(f"Error with filter selector {selector}: {e}")
                continue

    except Exception as e:
        print(f"Filter extraction error: {e}")
    
    print(f"Found {len(filters)} filter categories")
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






