from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup, Comment, Tag
import json
from typing import Optional, Any
import re

# Global variables
PRODUCT_INDICATORS = ['product', 'item', 'detail', 'main', 'content']
PRICE_PATTERNS = [
    r'^(?:\d{1,3}(?:[.,\s]\d{3})*(?:[.,]\d{2})?)\s*(?:DT|TND|D\.T)$',
    r'^(?:(?:[A-Z]{2,3}\s+)?[$€£])\s*(?:\d{1,3}(?:[.,\s]\d{3})*(?:[.,]\d{2})?)$',
    r'^(?:\d{1,3}(?:[.,\s]\d{3})*(?:[.,]\d{2})?)\s*[$€£]$'
]

def _get_node_weight(element) -> float:
    weight = 1.0

    if element.get('id') or element.get('class') or element.get('content'):
        for indicator in PRODUCT_INDICATORS:
            if indicator in str(element.get('id', '')).lower() or \
                    indicator in ' '.join(element.get('class', [])).lower():
                weight *= 1.5

    text = element.get_text(strip=True)
    weight *= min(len(text) / 100, 3)

    depth = len([p for p in element.parents])
    weight /= max(depth, 1)

    return weight

def _find_product_container(soup) -> BeautifulSoup:
    candidates = soup.find_all(['div', 'section', 'article', 'main'])
    max_weight = 0
    main_container = None

    for element in candidates:
        weight = _get_node_weight(element)
        if weight > max_weight:
            max_weight = weight
            main_container = element

    return main_container or soup

def get_price(soup):
    for tag in soup(['script', 'style', 'noscript', 'iframe',
                     'head', 'footer', 'nav', 'del', 'header', 'a', 'ol', 'ul', 'li']):
        tag.decompose()

    all_elements = soup.find_all(['div', 'span', 'p'], recursive=True)

    for element in all_elements:
        if isinstance(element, Tag):
            text = element.get_text().strip()

            for pattern in PRICE_PATTERNS:
                if re.match(pattern, text):
                    return text
    return None

def get_title(soup):
    try:
        try:
            return soup.find('meta', property='og:title')['content']
        except:
            pass
        try:
            return soup.find('meta', property='twitter:title')['content']
        except:
            pass
        try:
            return soup.find('meta', {'name': 'title'})['content']
        except:
            pass

        for tag in soup(['script', 'style', 'noscript', 'iframe',
                         'head', 'footer', 'nav', 'del', 'header', 'a', 'ol', 'ul', 'li']):
            tag.decompose()

        for comment in soup.find_all(string=lambda text: isinstance(text, Comment)):
            comment.extract()

        container = _find_product_container(soup)
        return container.find('h1').get_text(strip=True)

    except Exception as e:
        print(f"Error extracting prices: {e}")
        return ""

def extract_values(url: str, price_param: Optional[str] = None, descr_param: Optional[str] = None,
                  stock_param: Optional[str] = None) -> tuple[str | Any, str | Any, str | None, str | None]:
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=False)
        page = browser.new_page()
        try:
            page.goto(url, timeout=30000)
            page.wait_for_timeout(2000)
            html_content = page.content()
        except Exception as e:
            print(f"Error loading page: {e}")
            return "", "", "", ""
        finally:
            browser.close()

    soup = BeautifulSoup(html_content, 'lxml')
    soup1 = BeautifulSoup(html_content, 'lxml')

    price = get_price(soup1)
    title = get_title(soup)
    description = ''
    stock = ''

    if price_param:
        param_ = json.loads(price_param)
        attributes = json.loads(param_['attributes'])
        if attributes:
            element = soup.find(name=param_['tag'], attrs=attributes)
            currency_element = soup.find(name="meta", attrs={'property': 'product:price:currency'})
            if element and element.has_attr('content') and currency_element:
                price = f"{float(element['content']):,.3f}".replace(",", " ").replace(".", ",")
                price += " " + currency_element['content']
            elif element:
                price = element.get_text().strip()
        else:
            all_prices = soup1.find_all(lambda tag: tag.name == param_['tag'] and not tag.attrs)
            for element in all_prices:
                if isinstance(element, Tag):
                    text = element.get_text()
                    for pattern in PRICE_PATTERNS:
                        if re.match(pattern, text):
                            price = text.strip()
                            break

    if descr_param:
        descr_param_ = json.loads(descr_param)
        attributes = json.loads(descr_param_['attributes'])
        element = soup.find(name=descr_param_['tag'], attrs=attributes)
        if element:
            description = element['content'] if element.has_attr('content') else element.get_text()

    if stock_param:
        stock_param_ = json.loads(stock_param)
        attributes = json.loads(stock_param_['attributes'])
        element = soup.find(name=stock_param_['tag'], attrs=attributes)
        if element:
            stock = element['content'] if element.has_attr('content') else element.get_text()

    return price, title, description, stock

