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


def _extract_content_attributes(element) -> str:
    """Extract text from content-related attributes"""

    texts = []
    if element.has_attr('content'):
        texts.append(element['content'])
    return ' '.join(texts)
def clean_attrs(attrs):
    # List of attributes to exclude
    exclude_attrs = ['content', 'value', 'data-price', 'data-value', 'data-amount', 'id', 'data-product']
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
    soup1 = BeautifulSoup(html_content, 'lxml')
    for tag in soup(['script', 'style', 'noscript', 'iframe',
                      'head', 'footer', 'nav', 'del', 'header', 'a', 'ol', 'ul', 'li']):
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

            if is_price and element.attrs:
                # Add price element to list without checking for duplicates
                prices_list.append(element)
    description = []
    for element in soup1.find_all(lambda tag: any('description' in str(value).lower()
                                                 for value in tag.attrs.values())):
        content = ' '.join(element.get_text().split()).strip()
        attr_content = _extract_content_attributes(element)

        if content or attr_content:
            description.append({
                'tag_name': element.name,
                'attributes': clean_attrs(element.attrs),
                'text_content': content or attr_content,

            })
    # Convert list to results format
    results = []
    # More targeted approach focusing on common price-related attributes
    price_metas_str = list(map(lambda x: str(x), soup1.find_all('meta')))
    price_metas_str = list(filter(lambda x: 'price' in x.lower(), price_metas_str))
    price_metas = [BeautifulSoup(tag, 'lxml').meta for tag in price_metas_str]
    print(price_metas)

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

    return results,description

if __name__ == "__main__":
    url = 'https://spacenet.tn/lave-vaisselle-tunisie/46222-lave-vaisselle-semi-encastrable-hoover-16-couverts-inox-hdsn2d62.html'
    prices,description = extract_pattern(url)
    print(prices)
    print(description)


