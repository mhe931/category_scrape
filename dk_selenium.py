import json
from time import sleep
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def scrape_digikala_categories():
    # Set up Firefox options
    options = Options()
    options.add_argument("--headless")  # Run in headless mode
    driver = webdriver.Firefox(options=options)
    driver.maximize_window()

    try:
        # Navigate to Digikala's homepage
        driver.get("https://www.digikala.com/")
        sleep(5)  # Wait for the page to load

        # Dictionary to store categories and subcategories
        categories_data = {"categories": {}}

        # Find the main menu
        main_menu = driver.find_element(By.ID, "header")
        menu_items = main_menu.find_elements(By.XPATH, "//a[@class='menu__megamenu-tab--text']")

        for menu_item in menu_items:
            category_name = menu_item.text.strip()
            # Click on the category to load subcategories
            ActionChains(driver).move_to_element(menu_item).click().perform()
            sleep(2)

            # Get the subcategories for the current category
            subcategories = menu_item.find_elements(By.XPATH, "./following-sibling::div//ul/li/a")
            if subcategories:
                category_urls = []
                categories_data["categories"][category_name] = {
                    "url": menu_item.get_attribute("href"),
                    "subcategories": {}
                }

                for subcategory in subcategories:
                    subcategory_name = subcategory.text.strip()
                    subcategory_url = subcategory.get_attribute("href")
                    categories_data["categories"][category_name]["subcategories"][subcategory_name] = {
                        "url": subcategory_url
                    }

        return categories_data

    except Exception as e:
        print(f"An error occurred: {e}")
        return None
    finally:
        driver.quit()

def search_subcategories(categories_data, query):
    if not categories_data:
        return None

    matching_subcategories = []

    for category, data in categories_data["categories"].items():
        if "subcategories" in data:
            for subcategory_name, subcategory_data in data["subcategories"].items():
                if query.lower() in subcategory_name.lower():
                    matching_subcategories.append({
                        "category": category,
                        "subcategory": subcategory_name,
                        "url": subcategory_data["url"]
                    })

    return matching_subcategories

def save_to_json(data, filename):
    with open(filename, "w", encoding="utf-8") as json_file:
        json.dump(data, json_file, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    # Scrape categories and subcategories
    categories_data = scrape_digikala_categories()

    if categories_data:
        # Save all categories and subcategories to JSON
        save_to_json(categories_data, "digikala_categories.json")
        
        # Example: Search for subcategories containing "phone"
        search_query = "phone"
        results = search_subcategories(categories_data, search_query)
        
        if results:
            print(f"Found {len(results)} matching subcategories:")
            for result in results:
                print(f"Category: {result['category']}")
                print(f"Subcategory: {result['subcategory']}")
                print(f"URL: {result['url']}\n")
        else:
            print(f"No subcategories found matching '{search_query}'")

    else:
        print("Failed to retrieve categories data.")