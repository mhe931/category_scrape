from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.firefox import GeckoDriverManager
import json
import time
import random

BASE_URL = "https://www.amazon.com"
OUTPUT_FILE = "amazon_categories.json"

def setup_driver():
    """Setup and return a configured Firefox WebDriver"""
    firefox_options = Options()
    firefox_options.add_argument("--headless")
    firefox_options.add_argument("--width=1920")
    firefox_options.add_argument("--height=1080")
    
    # Add random user agent
    user_agent = get_random_user_agent()
    firefox_options.set_preference("general.useragent.override", user_agent)
    
    service = Service(GeckoDriverManager().install())
    driver = webdriver.Firefox(service=service, options=firefox_options)
    return driver

def get_random_user_agent():
    """Get a random user agent from a list of modern browsers"""
    user_agents = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:90.0) Gecko/20100101 Firefox/90.0',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:91.0) Gecko/20100101 Firefox/91.0',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:90.0) Gecko/20100101 Firefox/90.0',
        'Mozilla/5.0 (X11; Linux x86_64; rv:90.0) Gecko/20100101 Firefox/90.0',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
    ]
    return random.choice(user_agents)

def wait_and_get_element(driver, by, selector, timeout=10):
    """Wait for an element to be present and return it"""
    try:
        element = WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((by, selector))
        )
        return element
    except TimeoutException:
        print(f"Timeout waiting for element: {selector}")
        return None

def wait_and_get_elements(driver, by, selector, timeout=10):
    """Wait for elements to be present and return them"""
    try:
        elements = WebDriverWait(driver, timeout).until(
            EC.presence_of_all_elements_located((by, selector))
        )
        return elements
    except TimeoutException:
        print(f"Timeout waiting for elements: {selector}")
        return []

def hover_and_wait(driver, element, timeout=3):
    """Hover over an element and wait for potential dynamic content"""
    from selenium.webdriver.common.action_chains import ActionChains
    try:
        ActionChains(driver).move_to_element(element).perform()
        time.sleep(timeout)  # Wait for dynamic content to load
    except Exception as e:
        print(f"Error hovering over element: {e}")

def extract_categories():
    """Extract main categories from Amazon's homepage"""
    driver = setup_driver()
    categories = []
    
    try:
        # Go to Amazon homepage
        driver.get(BASE_URL)
        
        # Wait for and click the hamburger menu
        menu_button = wait_and_get_element(driver, By.ID, "nav-hamburger-menu")
        if not menu_button:
            return []
        menu_button.click()
        
        # Wait for the menu to load
        menu = wait_and_get_element(driver, By.ID, "hmenu-content")
        if not menu:
            return []
            
        # Get all main category elements
        main_categories = wait_and_get_elements(driver, By.CSS_SELECTOR, "ul.hmenu-content li a.hmenu-item")
        
        for cat in main_categories:
            try:
                cat_name = cat.text.strip()
                cat_url = cat.get_attribute("href")
                
                if cat_url and cat_name and not any(x in cat_name.lower() for x in ["sign in", "settings", "customer service"]):
                    cat_data = {
                        "name": cat_name,
                        "url": cat_url,
                        "subcategories": extract_subcategories(driver, cat)
                    }
                    categories.append(cat_data)
            except Exception as e:
                print(f"Error processing category: {e}")
                continue
                
    finally:
        driver.quit()
        
    return categories

def extract_subcategories(driver, category_element, depth=1, max_depth=2):
    """Extract subcategories by hovering over the category element"""
    if depth > max_depth:
        return []
        
    subcategories = []
    try:
        # Hover over the category element to show submenu
        hover_and_wait(driver, category_element)
        
        # Look for submenu items
        submenu = wait_and_get_elements(driver, By.CSS_SELECTOR, "ul.hmenu-submenu li a.hmenu-item")
        
        for subcat in submenu[:10]:  # Limit to first 10 to avoid too much processing
            try:
                name = subcat.text.strip()
                url = subcat.get_attribute("href")
                
                if url and name:
                    # Open subcategory in new tab to get filters
                    driver.execute_script('window.open(arguments[0]);', url)
                    driver.switch_to.window(driver.window_handles[-1])
                    
                    filters = extract_filters(driver)
                    
                    subcat_data = {
                        "name": name,
                        "url": url,
                        "filters": filters,
                        "subcategories": []  # We won't go deeper to avoid complexity
                    }
                    subcategories.append(subcat_data)
                    
                    # Close tab and switch back
                    driver.close()
                    driver.switch_to.window(driver.window_handles[0])
                    
            except Exception as e:
                print(f"Error processing subcategory: {e}")
                if len(driver.window_handles) > 1:
                    driver.close()
                    driver.switch_to.window(driver.window_handles[0])
                continue
                
    except Exception as e:
        print(f"Error extracting subcategories: {e}")
        
    return subcategories

def extract_filters(driver):
    """Extract available filters from the category/subcategory page"""
    filters = {}
    
    try:
        # Wait for filter sections to load
        filter_sections = wait_and_get_elements(driver, By.CSS_SELECTOR, "#filters .a-section")
        
        for section in filter_sections:
            try:
                # Get filter title
                title = section.find_element(By.CSS_SELECTOR, "h2, h3, h4").text.strip()
                
                # Get filter values
                values = []
                value_elements = section.find_elements(By.CSS_SELECTOR, "li span[class*='a-text-']")
                
                for val in value_elements:
                    value_text = val.text.strip()
                    if value_text and not value_text.startswith('$'):  # Skip price values
                        values.append(value_text)
                        
                if values:
                    filters[title] = values
                    
            except NoSuchElementException:
                continue
                
    except Exception as e:
        print(f"Error extracting filters: {e}")
        
    return filters

def save_categories(categories):
    """Save the extracted categories to a JSON file"""
    data = {
        "categories": categories,
        "metadata": {
            "total_categories": len(categories),
            "extraction_timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
    }
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def main():
    """Main function to orchestrate the scraping process"""
    print("Starting Amazon category extraction...")
    try:
        categories = extract_categories()
        if categories:
            save_categories(categories)
            print(f"Categories successfully saved to {OUTPUT_FILE}")
        else:
            print("Failed to extract categories")
    except Exception as e:
        print(f"Error during extraction: {e}")
    finally:
        print("Extraction process completed")

if __name__ == "__main__":
    main()







