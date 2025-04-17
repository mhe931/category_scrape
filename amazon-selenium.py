from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.common.action_chains import ActionChains
from webdriver_manager.firefox import GeckoDriverManager
import json
import time
import random

class AmazonCategoryScraper:
    def __init__(self):
        self.base_url = "https://www.amazon.com"
        self.output_file = "amazon_categories.json"
        self.driver = None

    def setup_driver(self):
        """Setup and return a configured Firefox WebDriver"""
        firefox_options = Options()
        # Temporarily disable headless mode for debugging
        # uncomment the line below if you want to run headless
        #firefox_options.add_argument("--headless")
        firefox_options.add_argument("--width=1920")
        firefox_options.add_argument("--height=1080")
        
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/109.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36'
        ]
        firefox_options.set_preference("general.useragent.override", random.choice(user_agents))
        
        # Disable webdriver mode
        firefox_options.set_preference("dom.webdriver.enabled", False)
        firefox_options.set_preference('useAutomationExtension', False)
        
        # Additional realistic browser settings
        firefox_options.set_preference("intl.accept_languages", "en-US, en")
        firefox_options.set_preference("browser.download.folderList", 2)
        firefox_options.set_preference("browser.helperApps.neverAsk.saveToDisk", "application/pdf")
        #firefox_options.set_preference("permissions.default.image", 2)  # Optional: Disable images for speed
        
        service = Service(GeckoDriverManager().install())
        self.driver = webdriver.Firefox(service=service, options=firefox_options)
        
        # Increase page load and implicit waits
        self.driver.set_page_load_timeout(60)
        self.driver.implicitly_wait(10)  # seconds

    def wait_for_element(self, by, selector, timeout=20):
        """Wait for an element to be present and return it"""
        try:
            element = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((by, selector))
            )
            return element
        except TimeoutException:
            print(f"Timeout waiting for element: {selector}")
            return None

    def wait_for_elements(self, by, selector, timeout=20, retries=5):
        """Wait for elements to be present and return them with retries"""
        for attempt in range(retries):
            try:
                # First wait for at least one element to be present
                WebDriverWait(self.driver, timeout).until(
                    EC.presence_of_element_located((by, selector))
                )
                
                # Then get all elements
                elements = WebDriverWait(self.driver, timeout).until(
                    EC.presence_of_all_elements_located((by, selector))
                )
                
                # Verify elements are actually visible and interactable
                visible_elements = [e for e in elements if e.is_displayed() and e.is_enabled()]
                if visible_elements:
                    return visible_elements
                
                # If no visible elements found, try scrolling
                self.driver.execute_script("window.scrollBy(0, 100);")
                time.sleep(1)
                
            except TimeoutException:
                if attempt < retries - 1:
                    print(f"Attempt {attempt + 1}/{retries} timed out waiting for elements: {selector}")
                time.sleep(2)
                continue
            except Exception as e:
                print(f"Error finding elements {selector}: {e}")
                break
                
        print(f"Failed to find elements after {retries} attempts: {selector}")
        return []

    def hover_element(self, element):
        """Hover over an element"""
        try:
            ActionChains(self.driver).move_to_element(element).perform()
            time.sleep(0.5)  # Short wait for submenu to appear
            # Random small delay to avoid detection
            time.sleep(random.uniform(0.2, 0.5))
        except Exception as e:
            print(f"Error hovering over element: {e}")

    def get_filters(self, url):
        """Extract filters from a category page"""
        filters = {}
        try:
            # Open category in current window
            self.driver.get(url)
            # Add random delay
            time.sleep(random.uniform(2, 4))

            # Look for filter sections in the left sidebar
            filter_sections = self.wait_for_elements(By.CSS_SELECTOR, ".a-section")
            
            for section in filter_sections:
                try:
                    # Get filter title
                    title_elem = section.find_element(By.CSS_SELECTOR, "h3")
                    title = title_elem.text.strip()
                    
                    # Get filter options
                    options = section.find_elements(By.CSS_SELECTOR, "li span")
                    filter_values = [opt.text.strip() for opt in options if opt.text.strip()]
                    
                    if title and filter_values:
                        filters[title] = filter_values
                except NoSuchElementException:
                    continue
                except Exception as e:
                    print(f"Error processing filter section: {e}")
                    continue
                
        except Exception as e:
            print(f"Error getting filters: {e}")
        
        return filters

    def get_subcategories(self, menu_item):
        """Extract subcategories from a menu item"""
        subcategories = []
        try:
            # Hover over the menu item to show subcategories
            self.hover_element(menu_item)
            
            # Get submenu container
            submenu = self.wait_for_elements(By.CSS_SELECTOR, "#nav-flyout-content .nav-subnav")
            if not submenu:
                return []

            # Get all subcategory links
            subcat_links = self.wait_for_elements(
                By.CSS_SELECTOR, 
                "#nav-flyout-content .nav-subnav a.nav-a"
            )
            
            for link in subcat_links:
                try:
                    name = link.text.strip()
                    url = link.get_attribute("href")
                    if name and url:
                        # Random delay between requests
                        time.sleep(random.uniform(1, 3))
                        filters = self.get_filters(url)
                        subcategories.append({
                            "name": name,
                            "url": url,
                            "filters": filters
                        })
                except Exception as e:
                    print(f"Error processing subcategory: {e}")
                    continue
                    
        except Exception as e:
            print(f"Error getting subcategories: {e}")
            
        return subcategories

    def scrape_categories(self):
        """Main method to scrape Amazon categories"""
        categories = []
        try:
            self.setup_driver()
            self.driver.get(self.base_url)
            
            # Wait for page to be fully loaded
            time.sleep(5)  # Increased initial wait
            
            # Modified selectors based on current Amazon structure
            selectors = [
                "#nav-main #nav-shop a.nav-a",
                "#nav-xshop a.nav-a",
                "#nav-main .nav-left a.nav-a",
                "#nav-hamburger-menu"
            ]
            
            menu_items = []
            for selector in selectors:
                menu_items = self.wait_for_elements(By.CSS_SELECTOR, selector)
                if menu_items:
                    break
            
            # If no menu items found, try clicking the hamburger menu
            if not menu_items:
                hamburger = self.wait_for_element(By.CSS_SELECTOR, "#nav-hamburger-menu")
                if hamburger:
                    hamburger.click()
                    time.sleep(2)  # Wait for menu to expand
                    menu_items = self.wait_for_elements(By.CSS_SELECTOR, ".hmenu-item")
            
            if not menu_items:
                print("Could not find category menu items with any known selector")
                return categories
            
            for item in menu_items:
                try:
                    name = item.text.strip()
                    url = item.get_attribute("href")
                    
                    if name and url:
                        # Random delay between category processing
                        time.sleep(random.uniform(1, 3))
                        category = {
                            "name": name,
                            "url": url,
                            "subcategories": self.get_subcategories(item)
                        }
                        categories.append(category)
                        
                except Exception as e:
                    print(f"Error processing category: {e}")
                    continue
                    
        except Exception as e:
            print(f"Error during scraping: {e}")
        finally:
            if self.driver:
                self.driver.quit()
                
        return categories

    def save_to_json(self, data):
        """Save the scraped data to a JSON file"""
        output = {
            "categories": data,
            "metadata": {
                "total_categories": len(data),
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            }
        }
        
        with open(self.output_file, 'w', encoding='utf-8') as f:
            json.dump(output, f, ensure_ascii=False, indent=2)

def main():
    scraper = AmazonCategoryScraper()
    print("Starting Amazon category scraping...")
    categories = scraper.scrape_categories()
    
    if categories:
        scraper.save_to_json(categories)
        print(f"Categories successfully saved to {scraper.output_file}")
    else:
        print("No categories were extracted")

if __name__ == "__main__":
    main()