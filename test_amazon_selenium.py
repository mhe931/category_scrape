import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from amazon_selenium import AmazonCategoryScraper

@pytest.fixture
def scraper():
    return AmazonCategoryScraper()

def test_setup_driver(scraper):
    """Test that the driver is properly initialized"""
    scraper.setup_driver()
    assert scraper.driver is not None
    scraper.driver.quit()

def test_wait_for_element(scraper):
    """Test waiting for an element"""
    scraper.setup_driver()
    try:
        scraper.driver.get(scraper.base_url)
        element = scraper.wait_for_element(By.CSS_SELECTOR, "#nav-main")
        assert element is not None
        assert isinstance(element, WebElement)
    finally:
        scraper.driver.quit()

def test_wait_for_elements(scraper):
    """Test waiting for multiple elements"""
    scraper.setup_driver()
    try:
        scraper.driver.get(scraper.base_url)
        elements = scraper.wait_for_elements(By.CSS_SELECTOR, "#nav-main a")
        assert isinstance(elements, list)
        assert len(elements) > 0
        assert all(isinstance(e, WebElement) for e in elements)
    finally:
        scraper.driver.quit()

def test_get_filters_structure(scraper):
    """Test that get_filters returns the expected data structure"""
    scraper.setup_driver()
    try:
        # Test with a known category URL
        test_url = "https://www.amazon.com/s?rh=n%3A172282"  # Electronics category
        filters = scraper.get_filters(test_url)
        
        assert isinstance(filters, dict)
        # Check that at least some common filter categories exist
        common_filters = ["Brand", "Price", "Condition"]
        assert any(filter_name in filters.keys() for filter_name in common_filters)
        
        # Check filter values structure
        for filter_name, values in filters.items():
            assert isinstance(filter_name, str)
            assert isinstance(values, list)
            assert len(values) > 0
            assert all(isinstance(v, str) for v in values)
    finally:
        scraper.driver.quit()

def test_scrape_categories_structure(scraper):
    """Test that scrape_categories returns the expected data structure"""
    categories = scraper.scrape_categories()
    
    assert isinstance(categories, list)
    assert len(categories) > 0
    
    for category in categories:
        assert isinstance(category, dict)
        assert "name" in category
        assert "url" in category
        assert "subcategories" in category
        assert isinstance(category["name"], str)
        assert isinstance(category["url"], str)
        assert isinstance(category["subcategories"], list)
        
        for subcategory in category["subcategories"]:
            assert isinstance(subcategory, dict)
            assert "name" in subcategory
            assert "url" in subcategory
            assert "filters" in subcategory
            assert isinstance(subcategory["filters"], dict)

def test_invalid_url_handling(scraper):
    """Test that the scraper handles invalid URLs gracefully"""
    scraper.setup_driver()
    try:
        invalid_url = "https://www.amazon.com/nonexistent-category-12345"
        filters = scraper.get_filters(invalid_url)
        assert isinstance(filters, dict)
        assert len(filters) == 0  # Should return empty dict for invalid URL
    finally:
        scraper.driver.quit()

def test_hover_element(scraper):
    """Test hover functionality"""
    scraper.setup_driver()
    try:
        scraper.driver.get(scraper.base_url)
        element = scraper.wait_for_element(By.CSS_SELECTOR, "#nav-main")
        assert element is not None
        # Should not raise any exceptions
        scraper.hover_element(element)
    finally:
        scraper.driver.quit()

def test_save_to_json(scraper, tmp_path):
    """Test JSON saving functionality"""
    # Create test data
    test_data = [
        {
            "name": "Test Category",
            "url": "https://example.com",
            "subcategories": []
        }
    ]
    
    # Temporarily change output file to a test location
    original_output = scraper.output_file
    test_output = tmp_path / "test_output.json"
    scraper.output_file = str(test_output)
    
    try:
        scraper.save_to_json(test_data)
        assert test_output.exists()
        
        # Verify file content
        import json
        with open(test_output, 'r', encoding='utf-8') as f:
            saved_data = json.load(f)
        
        assert "categories" in saved_data
        assert "metadata" in saved_data
        assert len(saved_data["categories"]) == 1
        assert saved_data["metadata"]["total_categories"] == 1
    finally:
        scraper.output_file = original_output

def test_get_subcategories_error_handling(scraper):
    """Test error handling in get_subcategories method"""
    scraper.setup_driver()
    try:
        # Test with an invalid element that can't be hovered
        from selenium.webdriver.remote.webelement import WebElement
        from unittest.mock import Mock
        mock_element = Mock(spec=WebElement)
        
        # This should return an empty list instead of raising an exception
        result = scraper.get_subcategories(mock_element)
        assert isinstance(result, list)
        assert len(result) == 0
    finally:
        scraper.driver.quit()

def test_wait_for_elements_with_retries(scraper):
    """Test that wait_for_elements retries on failure"""
    scraper.setup_driver()
    try:
        # Use a selector that doesn't exist to trigger retries
        elements = scraper.wait_for_elements(
            By.CSS_SELECTOR, 
            "#non-existent-element", 
            timeout=1,  # Short timeout for faster test
            retries=2
        )
        assert isinstance(elements, list)
        assert len(elements) == 0  # Should return empty list after all retries fail
    finally:
        scraper.driver.quit()

def test_alternative_selectors(scraper):
    """Test that alternative selectors are tried when main one fails"""
    scraper.setup_driver()
    try:
        scraper.driver.get(scraper.base_url)
        
        # Try getting menu items - should try multiple selectors
        menu_items = []
        selectors = [
            "#nav-main #nav-shop a[class*='nav-a']",
            "#nav-xshop a[class*='nav-a']",
            "#nav-main .nav-left a[class*='nav-a']",
            "#nav-hamburger-menu"
        ]
        
        for selector in selectors:
            items = scraper.wait_for_elements(By.CSS_SELECTOR, selector, timeout=5)
            if items:
                menu_items = items
                break
                
        # We should find at least some menu items with one of the selectors
        assert len(menu_items) > 0
        
    finally:
        scraper.driver.quit()

