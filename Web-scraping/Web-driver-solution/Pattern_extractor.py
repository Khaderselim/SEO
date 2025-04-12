from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
from bs4 import Tag
import re

PRICE_PATTERNS = [
    # Matches: 1234.56 DT, 1,234.56 TND, 1 234.56 D.T
    r'^(?:\d{1,3}(?:[.,\s]\d{3})*(?:[.,]\d{2})?)\s*(?:DT|TND|D\.T)$',

    # Matches: $1234.56, €1,234.56, £1 234.56 AND US $145.95, EUR €100, etc.
    r'^(?:(?:[A-Z]{2,3}\s+)?[$€£])\s*(?:\d{1,3}(?:[.,\s]\d{3})*(?:[.,]\d{2})?)$',

    # Matches: 1234.56$, 1,234.56€, 1 234.56£
    r'^(?:\d{1,3}(?:[.,\s]\d{3})*(?:[.,]\d{2})?)\s*[$€£]$'
]


def _extract_content_attributes(element) -> str:
    """
    Extract text from content-related attributes
    Args:
        element: The HTML element to extract from

    Returns: str: The extracted text

    """

    texts = []
    if element.has_attr('content'):
        texts.append(element['content'])
    return ' '.join(texts)
def clean_attrs(attrs):
    """
    Clean attributes by removing attributes that have unique values
        (e.g., id, href)

    Args:
        attrs:  The attributes of the HTML element

    Returns: dict: The cleaned attributes

    """
    # List of attributes to exclude
    exclude_attrs = ['content', 'value', 'data-price', 'data-value', 'data-amount', 'id', 'data-product', 'href']
    return {k: v for k, v in attrs.items() if k not in exclude_attrs}
def clean_stock_attrs(attrs):
    """
    Clean attributes for stock by removing attributes that have unique values
        (e.g., id, href)
    This is a more specific version of clean_attrs, focusing on stock-related attributes.
    Args:
        attrs: The attributes of the HTML element

    Returns: dict: The cleaned attributes
    """
    # List of attributes to exclude
    exclude_attrs = ['content', 'value', 'data-price', 'data-value', 'data-amount',
                    'id', 'data-product', 'href', 'class', 'title']
    return {k: v for k, v in attrs.items() if k not in exclude_attrs}


def extract_pattern(url: str):
    """
    Extract price patterns from the given URL using Playwright and BeautifulSoup.
    Args:
        url: The URL to extract data from

    Returns: list: A list of dictionaries containing product information

    """
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=False) # Set headless to True for faster execution, but it's easily blocked by some sites
        page = browser.new_page() # Open a new browser page
        try:
            page.goto(url, timeout=30000) # Navigate to the URL with a timeout of 30 seconds (adjust as needed)
            page.wait_for_timeout(2000) # Wait for 2 seconds to allow the page to load
            html_content = page.content() # Get the HTML content of the page
        except Exception as e:
            print(f"Error loading page: {e}")
            return []
        finally:
            browser.close() # Close the browser after extraction

    soup = BeautifulSoup(html_content, 'lxml') # Parse the HTML content for prices extraction with BeautifulSoup
    soup1 = BeautifulSoup(html_content, 'lxml') # Parse the HTML content for description and stock extraction with BeautifulSoup
    for tag in soup(['script', 'style', 'noscript', 'iframe',
                      'head', 'footer', 'nav', 'del', 'header', 'a', 'ol', 'ul', 'li']):
        tag.decompose() # Remove unnecessary tags from the soup
    for tag in soup1(['script', 'style', 'noscript', 'iframe']):
        tag.decompose() # Remove unnecessary tags from the soup1
    # List to store all found prices
    prices_list = []

    # Get all elements
    all_elements = soup.find_all(True, recursive=True)

    for element in all_elements:
        if isinstance(element, Tag):
            # Get text and clean it from extra spaces
            text = element.get_text().strip()

            # Check if the text is exactly a price format
            is_price = False
            for pattern in PRICE_PATTERNS:
                if re.match(pattern, text):
                    is_price = True

            if is_price and element.attrs:
                # Add price element to list without checking for duplicates
                prices_list.append(element)

    # Extract description information
    description = []
    # Get all elements with 'description' in their attributes
    for element in soup1.find_all(lambda tag: any('description' in str(value).lower()
                                                 for value in tag.attrs.values())):
        content = ' '.join(element.get_text().split()).strip()
        attr_content = _extract_content_attributes(element)
        # Check if the content or attribute content is not empty
        if content or attr_content:
            description.append({
                'tag_name': element.name,
                'attributes': clean_attrs(element.attrs),
                'text_content': content or attr_content,

            })

    # Extract stock information
    stock = []
    # Get all elements with 'stock' in their attributes, excluding 'main' as a tag and 'stockage' as a keyword
    for element in soup1.find_all(lambda tag: tag.name != 'main' and any('stock' in str(value).lower()
                                                  and 'stockage' not in str(value).lower()
                                                 for value in tag.attrs.values())):
        content = ' '.join(element.get_text().split()).strip()
        attr_content = _extract_content_attributes(element)
        # Check if the content or attribute content is not empty
        if content or attr_content:
            stock.append({
                'tag_name': element.name,
                'attributes': clean_stock_attrs(element.attrs),
                'text_content': content or attr_content,

            })

    results = []
    # Extract price information from meta tags for more accurate results
    price_metas_str = list(map(lambda x: str(x), soup1.find_all('meta')))
    price_metas_str = list(filter(lambda x: 'price' in x.lower(), price_metas_str))
    price_metas = [BeautifulSoup(tag, 'lxml').meta for tag in price_metas_str]
    # Extract price information from the soup1 and merge it with the prices_list
    for meta in price_metas:
        if meta.has_attr('content') :
            try:
                results.append({
                    'price': f"{float(meta['content']):,.3f}".replace(",", " ").replace(".", ",") + " DT",
                    'tag_name': meta.name,
                    'attributes': clean_attrs(meta.attrs)
                })
            except:
                pass
    for element in prices_list:
        results.append({
            'price': element.get_text().strip(),
            'tag_name': element.name,
            'attributes': clean_attrs(element.attrs)
        })

    return results,description,stock # Return the results as a tuple of prices, description, and stock

if __name__ == "__main__":
    url = 'https://wiki.tn/hisense-55-a6k-televiseur-4k-uhd-smart-tv/'
    prices,description,stock = extract_pattern(url)
    print(prices)
    print(description)
    print(stock)


