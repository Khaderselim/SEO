#{"tag":"span","attributes":"{\"class\":[\"price\"],\"itemprop\":\"price\"}"}
import json
from typing import Any, Optional

from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup, Comment ,Tag
import re


class DOMPriceExtractor:
    def __init__(self):
        self.product_indicators = ['product', 'item', 'detail', 'main', 'content']
        self.PRICE_PATTERNS = [
    # Matches: 1234.56 DT, 1,234.56 TND, 1 234.56 D.T
    r'^(?:\d{1,3}(?:[.,\s]\d{3})*(?:[.,]\d{2})?)\s*(?:DT|TND|D\.T)$',

    # Matches: $1234.56, €1,234.56, £1 234.56 AND US $145.95, EUR €100, etc.
    r'^(?:(?:[A-Z]{2,3}\s+)?[$€£])\s*(?:\d{1,3}(?:[.,\s]\d{3})*(?:[.,]\d{2})?)$',

    # Matches: 1234.56$, 1,234.56€, 1 234.56£
    r'^(?:\d{1,3}(?:[.,\s]\d{3})*(?:[.,]\d{2})?)\s*[$€£]$'
]

    def _get_node_weight(self, element) -> float:
        """Calculate importance weight of a DOM node"""
        weight = 1.0

        # Check element attributes
        if element.get('id') or element.get('class') or element.get('content'):
            for indicator in self.product_indicators:
                if indicator in str(element.get('id', '')).lower() or \
                   indicator in ' '.join(element.get('class', [])).lower():
                    weight *= 1.5

        # Check content size
        text = element.get_text(strip=True)
        weight *= min(len(text) / 100, 3)

        # Check depth in DOM
        depth = len([p for p in element.parents])
        weight /= max(depth, 1)

        return weight

    def _find_product_container(self, soup) -> BeautifulSoup:
        """Find the main product container using weighted scoring"""
        candidates = soup.find_all(['div', 'section', 'article', 'main'])
        max_weight = 0
        main_container = None

        for element in candidates:
            weight = self._get_node_weight(element)
            if weight > max_weight:
                max_weight = weight
                main_container = element

        return  main_container or soup
    def get_price(self,soup):
        for tag in soup(['script', 'style', 'noscript', 'iframe',
                          'head', 'footer', 'nav', 'del', 'header', 'a', 'ol', 'ul', 'li']):
            tag.decompose()
        # Dictionary to store unique prices (key: normalized price, value: best tag)

        # Get all elements
        all_elements = soup.find_all(['div', 'span', 'p'], recursive=True)

        for element in all_elements:
            if isinstance(element, Tag):
                # Get text and clean it
                text = element.get_text().strip()

                # Skip empty text or extremely long text (likely containers)

                # Check if the text is exactly a price format
                is_price = False
                for pattern in self.PRICE_PATTERNS:
                    if re.match(pattern, text):
                        is_price = True

                if is_price:
                    return element.get_text().strip()




    def get_title(self, soup):
        try:
            # Try to extract title from meta tags
            try:
                title = soup.find('meta', property='og:title')['content']
                return title
            except:
                pass
            try:
                title = soup.find('meta', property='twitter:title')['content']
                return title
            except:
                pass
            try:
                title = soup.find('meta', {'name': 'title'})['content']
                return title
            except:
                pass

            # Clean up DOM
            for tag in soup(['script', 'style', 'noscript', 'iframe',
                              'head', 'footer', 'nav', 'del', 'header', 'a', 'ol', 'ul', 'li']):
                tag.decompose()

            for comment in soup.find_all(string=lambda text: isinstance(text, Comment)):
                comment.extract()

            container = self._find_product_container(soup)
            seen_title = container.find('h1').get_text(strip=True)

            return seen_title

        except Exception as e:
            print(f"Error extracting prices: {e}")
            return ""

    def extract_prices(self, url: str, param: Optional[str] = None, descr_param: Optional[str] = None) -> tuple[str | Any, str | Any, str | None]:
        """Main price extraction method"""
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
        price = self.get_price(soup1)
        title = self.get_title(soup)
        description=''
        if param:
            param_ = json.loads(param)
            attributes = json.loads(param_['attributes'])
            if attributes:
                element = soup.find(name=param_['tag'], attrs=attributes)
                if(element.has_attr('content')):

                    price = f"{float(element['content']):,.3f}".replace(",", " ").replace(".", ",") + " DT"
                else:
                    price = element.get_text().strip()
            else:
                # Find elements without any attributes
                all_prices = soup1.find_all(lambda tag: tag.name == param_['tag'] and not tag.attrs)
                for element in all_prices:
                    if(isinstance(element,Tag)):
                        text = element.get_text()
                        for pattern in self.PRICE_PATTERNS:
                            if re.match(pattern, text):
                                price = element.get_text().strip()
                                break
        if descr_param:
            descr_param_ = json.loads(descr_param)
            attributes = json.loads(descr_param_['attributes'])
            element = soup.find(name=descr_param_['tag'], attrs=attributes)
            if(element.has_attr('content')):
                description = element['content']
            else:
                description = element.get_text()


        return  price,title,description


# Usage
if __name__ == "__main__":
    extractor = DOMPriceExtractor()
    url = "https://spacenet.tn/lave-vaisselle-tunisie/46222-lave-vaisselle-semi-encastrable-hoover-16-couverts-inox-hdsn2d62.html"
    param = json.dumps({"tag":"meta","attributes":"{\"property\":[\"product:price:amount\"]}"})
    descr_param = json.dumps({"tag":"meta","attributes":"{\"property\":\"og:description\"}"})

    prices,title,param = extractor.extract_prices(url,param=param,descr_param=descr_param)
    print(f"Found title: {title}\nFound prices: {prices}\nFound description: {param}")