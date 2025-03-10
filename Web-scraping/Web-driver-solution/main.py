from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
from bs4 import Tag
import re

# Stricter price patterns
PRICE_PATTERNS = [
    # Matches: 1234.56 DT, 1,234.56 TND, 1 234.56 D.T
    r'^(?:\d{1,3}(?:[.,\s]\d{3})*(?:[.,]\d{2})?)\s*(?:DT|TND|D\.T)$',

    # Matches: $1234.56, €1,234.56, £1 234.56 AND US $145.95, EUR €100, etc.
    r'^(?:(?:[A-Z]{2,3}\s+)?[$€£])\s*(?:\d{1,3}(?:[.,\s]\d{3})*(?:[.,]\d{2})?)$',

    # Matches: 1234.56$, 1,234.56€, 1 234.56£
    r'^(?:\d{1,3}(?:[.,\s]\d{3})*(?:[.,]\d{2})?)\s*[$€£]$'
]

def clean_attrs(attrs):
    # List of attributes to exclude
    exclude_attrs = ['content', 'value', 'data-price', 'data-value', 'data-amount']
    return {k: v for k, v in attrs.items() if k not in exclude_attrs}

def extract_pattern(url: str):
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=False)
        page = browser.new_page()
        try:
            page.goto(url, timeout=30000)
            page.wait_for_timeout(2000)
            html_content = page.content()
        except Exception as e:
            print(f"Error loading page: {e}")
            return []
        finally:
            browser.close()

    soup = BeautifulSoup(html_content, 'lxml')
    for tag in soup(['script', 'style', 'noscript', 'iframe',
                     'meta', 'head', 'footer', 'nav', 'del', 'header', 'a', 'ol', 'ul', 'li']):
        tag.decompose()
    # List to store all found prices
    prices_list = []

    # Get all elements
    all_elements = soup.find_all(True, recursive=True)

    for element in all_elements:
        if isinstance(element, Tag):
            # Get text and clean it
            text = element.get_text().strip()

            # Check if the text is exactly a price format
            is_price = False
            for pattern in PRICE_PATTERNS:
                if re.match(pattern, text):
                    is_price = True
                    print(element)

            if is_price and element.attrs:
                # Add price element to list without checking for duplicates
                prices_list.append(element)

    # Convert list to results format
    results = []
    for element in prices_list:
        results.append({
            'price': element.get_text().strip(),
            'tag_name': element.name,
            'attributes': clean_attrs(element.attrs)
        })

    return results

