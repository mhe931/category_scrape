import requests
from bs4 import BeautifulSoup
import json

BASE_URL = "https://www.digikala.com"

def get_soup(url):
    headers = {
        'User-Agent': 'Mozilla/5.0'
    }
    res = requests.get(url, headers=headers)
    return BeautifulSoup(res.text, 'html.parser')

def extract_categories():
    soup = get_soup(BASE_URL)
    categories = []

    nav_items = soup.select('nav [class*=MegaMenuCategory]')  # Adjust selector based on actual site
    for main_cat in nav_items:
        cat_name = main_cat.get_text(strip=True)
        cat_url = BASE_URL + main_cat['href']
        cat_data = {
            'name': cat_name,
            'subcategories': extract_subcategories(cat_url)
        }
        categories.append(cat_data)

    return categories

def extract_subcategories(url, depth=1, max_depth=3):
    if depth > max_depth:
        return []

    soup = get_soup(url)
    subcats = []
    sub_items = soup.select('ul a')  # Needs to be customized based on Digikala's subcategory layout

    for item in sub_items[:5]:  # Limit to avoid spam
        name = item.get_text(strip=True)
        link = BASE_URL + item['href']
        subcat = {
            'name': name,
            'subcategories': extract_subcategories(link, depth + 1),
            'filters': extract_filters(link)
        }
        subcats.append(subcat)

    return subcats

def extract_filters(url):
    soup = get_soup(url)
    filters = {}

    filter_blocks = soup.select('[data-testid="filter"]')  # Adjust selector
    for block in filter_blocks:
        label = block.find('h4')
        if not label:
            continue
        key = label.text.strip()
        values = [li.get_text(strip=True) for li in block.select('ul li') if li.get_text(strip=True)]
        if values:
            filters[key] = values

    return filters

def main():
    data = {
        "categories": extract_categories()
    }
    with open('digikala_categories.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    main()
