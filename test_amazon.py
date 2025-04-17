import pytest
from unittest.mock import patch, MagicMock
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import amazon

@pytest.fixture
def mock_driver():
    """Create a mock Selenium WebDriver"""
    driver = MagicMock()
    
    # Mock the find_element and find_elements methods
    def mock_find_element(by, selector):
        if selector == "nav-hamburger-menu":
            return MagicMock(text="Menu")
        elif selector == "hmenu-content":
            return MagicMock(text="Menu Content")
        elif "h2, h3, h4" in selector:
            return MagicMock(text="Brand")
        raise NoSuchElementException(f"Could not find element: {selector}")
    
    def mock_find_elements(by, selector):
        if "hmenu-content li a.hmenu-item" in selector:
            return [
                MagicMock(text="Category 1", get_attribute=lambda x: "http://amazon.com/cat1"),
                MagicMock(text="Category 2", get_attribute=lambda x: "http://amazon.com/cat2")
            ]
        elif "hmenu-submenu li a.hmenu-item" in selector:
            return [
                MagicMock(text="Subcategory 1", get_attribute=lambda x: "http://amazon.com/subcat1"),
                MagicMock(text="Subcategory 2", get_attribute=lambda x: "http://amazon.com/subcat2")
            ]
        elif "filters .a-section" in selector:
            return [MagicMock(
                find_element=lambda by, selector: MagicMock(text="Brand"),
                find_elements=lambda by, selector: [
                    MagicMock(text="Brand 1"),
                    MagicMock(text="Brand 2")
                ]
            )]
        return []
    
    driver.find_element = mock_find_element
    driver.find_elements = mock_find_elements
    
    # Mock window handles
    driver.window_handles = ["main"]
    driver.current_window_handle = "main"
    
    return driver

@pytest.fixture
def mock_webdriver_wait():
    """Create a mock WebDriverWait"""
    class MockWebDriverWait:
        def __init__(self, driver, timeout):
            self.driver = driver
            self.timeout = timeout
            
        def until(self, condition):
            return self.driver.find_element(By.ID, "mock-element")
    
    return MockWebDriverWait

def test_setup_driver():
    """Test the setup_driver function"""
    with patch('selenium.webdriver.Firefox') as mock_firefox:
        driver = amazon.setup_driver()
        assert driver is not None
        mock_firefox.assert_called_once()

def test_extract_categories(mock_driver):
    """Test the extract_categories function"""
    with patch('amazon.setup_driver', return_value=mock_driver):
        categories = amazon.extract_categories()
        assert isinstance(categories, list)
        assert len(categories) == 2
        assert all('name' in cat for cat in categories)
        assert all('url' in cat for cat in categories)
        assert all('subcategories' in cat for cat in categories)

def test_extract_subcategories(mock_driver):
    """Test the extract_subcategories function"""
    category_element = MagicMock()
    subcategories = amazon.extract_subcategories(mock_driver, category_element)
    assert isinstance(subcategories, list)
    assert len(subcategories) == 2
    assert all('name' in subcat for subcat in subcategories)
    assert all('url' in subcat for subcat in subcategories)
    assert all('filters' in subcat for subcat in subcategories)

def test_extract_filters(mock_driver):
    """Test the extract_filters function"""
    filters = amazon.extract_filters(mock_driver)
    assert isinstance(filters, dict)
    assert 'Brand' in filters
    assert len(filters['Brand']) == 2
    assert 'Brand 1' in filters['Brand']
    assert 'Brand 2' in filters['Brand']

def test_wait_and_get_element(mock_driver, mock_webdriver_wait):
    """Test the wait_and_get_element function"""
    with patch('selenium.webdriver.support.ui.WebDriverWait', mock_webdriver_wait):
        element = amazon.wait_and_get_element(mock_driver, By.ID, "test-id")
        assert element is not None

def test_wait_and_get_element_timeout(mock_driver):
    """Test wait_and_get_element with timeout"""
    def mock_until(condition):
        raise TimeoutException("Timeout")
        
    mock_wait = MagicMock()
    mock_wait.until = mock_until
    
    with patch('selenium.webdriver.support.ui.WebDriverWait', return_value=mock_wait):
        element = amazon.wait_and_get_element(mock_driver, By.ID, "test-id")
        assert element is None

def test_hover_and_wait(mock_driver):
    """Test the hover_and_wait function"""
    element = MagicMock()
    with patch('selenium.webdriver.common.action_chains.ActionChains') as mock_actions:
        amazon.hover_and_wait(mock_driver, element, timeout=0)
        mock_actions.assert_called_once_with(mock_driver)
        mock_actions.return_value.move_to_element.assert_called_once_with(element)
        mock_actions.return_value.perform.assert_called_once()


