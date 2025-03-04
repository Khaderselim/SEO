from typing import Any

from bs4 import BeautifulSoup, Comment
import re
import cloudscraper


class DOMPriceExtractor:
    def __init__(self):
        self.price_patterns = r'\d{1,}(?:[\s.,]\d{3})*(?:[.,]\d+)?'  # Match numbers only
        self.currency_pattern = r'(?:DT|TND)'  # Currency pattern
        self.product_indicators = ['product', 'item', 'detail', 'main', 'content']
        self.price_pattern = r'\d{1,}(?:[\s.,]\d{3})*(?:[.,]\d+)?\s*?(?:DT|TND)'

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
        try:
            for a_tag in soup.find_all('a'):
                next_sibling = a_tag.find_next_sibling()
                if next_sibling and re.search(self.price_patterns, next_sibling.get_text(strip=True)):
                    next_sibling.decompose()
            # Clean up DOM
            for tag in soup(['script', 'style', 'noscript', 'iframe',
                             'meta', 'head', 'footer', 'nav', 'del','header','a','ol','ul','li']):
                tag.decompose()

            for comment in soup.find_all(string=lambda text: isinstance(text, Comment)):
                comment.extract()

            container = self._find_product_container(soup)
            seen_prices = ''
            try:
                price_spans = container.find_all('span', attrs={'content': True})
                for span in price_spans:
                    price_text = span.get_text(strip=True)
                    if price_text and re.findall(self.price_patterns, price_text):
                        return price_text

            except:
                pass

            # Find all elements with text
            elements = container.find_all(string=True)
            for i, element in enumerate(elements):
                if element.strip():  # Skip empty elements
                    price_matches = re.findall(self.price_patterns, element)
                    if price_matches and i + 1 < len(elements):
                        next_element = elements[i + 1]
                        if re.search(self.currency_pattern, str(next_element)):
                            for price in price_matches:
                                formatted_price = price.strip()
                                if formatted_price :
                                    return formatted_price+str(next_element)

            for element in elements:
                matches = re.findall(self.price_pattern, element)
                for match in matches:
                    return match

            return seen_prices

        except Exception as e:
            print(f"Error extracting prices: {e}")
            return ""

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
                             'meta', 'head', 'footer', 'nav', 'del', 'header', 'a', 'ol', 'ul', 'li']):
                tag.decompose()

            for comment in soup.find_all(string=lambda text: isinstance(text, Comment)):
                comment.extract()

            container = self._find_product_container(soup)
            seen_title = container.find('h1').get_text(strip=True)

            return seen_title

        except Exception as e:
            print(f"Error extracting prices: {e}")
            return ""

    def extract_prices(self, url: str) -> tuple[str | Any, str | Any]:
        """Main price extraction method"""
        scraper = cloudscraper.create_scraper()
        html_content = scraper.get(url).content
        soup = BeautifulSoup(html_content, 'html.parser')
        soup1 = BeautifulSoup(html_content, 'html.parser')
        return  self.get_price(soup1),self.get_title(soup)


# Usage
if __name__ == "__main__":
    extractor = DOMPriceExtractor()
    url = "https://animalzone.tn/shampoing-chien/3510-bioline-shampoing-a-l-huile-de-neem-1l-oc22-6970117120868.html"
    prices,title = extractor.extract_prices(url)
    print(f"Found title: {title}\nFound prices: {prices}")