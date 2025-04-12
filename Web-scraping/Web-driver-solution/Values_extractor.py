import json
from typing import Any, Optional

from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup, Comment ,Tag
import re


class DOMExtractor:
    """
    A class to extract prices and titles from a webpage using DOM analysis.
    """
    def __init__(self):
        """
        Initialize the DOMExtractor with default settings.
        """
        self.product_indicators = ['product', 'item', 'detail', 'main', 'content'] # Indicators to identify product-related elements
        self.PRICE_PATTERNS = [
            # Matches: 1234.56 DT, 1,234.56 TND, 1 234.56 D.T
            r'^(?:\d{1,3}(?:[.,\s]\d{3})*(?:[.,]\d{2})?)\s*(?:DT|TND|D\.T)$',

            # Matches: $1234.56, €1,234.56, £1 234.56 AND US $145.95, EUR €100, etc.
            r'^(?:(?:[A-Z]{2,3}\s+)?[$€£])\s*(?:\d{1,3}(?:[.,\s]\d{3})*(?:[.,]\d{2})?)$',

            # Matches: 1234.56$, 1,234.56€, 1 234.56£
            r'^(?:\d{1,3}(?:[.,\s]\d{3})*(?:[.,]\d{2})?)\s*[$€£]$'
        ]

    def _get_node_weight(self, element) -> float:
        """
        Calculate importance weight of a DOM node.
        This function assigns a weight to a DOM node based on its attributes, content size, and depth in the DOM tree.
        The weight is used to identify the most relevant elements for price extraction.
        The higher the weight, the more important the element is considered to be.

        Args:
            element: The HTML element to analyze.

        Returns: float: The importance weight of the element.

        """

        weight = 1.0 # Default weight

        # Check element attributes
        if element.get('id') or element.get('class') or element.get('content'):
            for indicator in self.product_indicators:
                if indicator in str(element.get('id', '')).lower() or \
                        indicator in ' '.join(element.get('class', [])).lower():
                    weight *= 1.5  # Increase weight

        # Check content size
        text = element.get_text(strip=True)
        weight *= min(len(text) / 100, 3) # Normalize weight based on text length

        # Check depth in DOM
        depth = len([p for p in element.parents])
        weight /= max(depth, 1) # Avoid division by zero

        return weight

    def _find_product_container(self, soup) -> BeautifulSoup:
        """
        Find the main product container using weighted scoring.
        Args:
            soup: The BeautifulSoup object representing the parsed HTML content.

        Returns: BeautifulSoup: The main product container.

        """
        candidates = soup.find_all(['div', 'section', 'article', 'main']) # Possible product containers
        max_weight = 0  # Initialize maximum weight
        main_container = None # Initialize main container
        # Iterate through candidates to find the one with the highest weight
        for element in candidates:
            weight = self._get_node_weight(element) # Calculate weight
            if weight > max_weight:
                max_weight = weight
                main_container = element
        # Return the main container or the entire soup if no suitable container is found
        return main_container or soup

    def get_price(self, soup):
        """
        Extract price from the given soup object.
        Args:
            soup: The BeautifulSoup object representing the parsed HTML content.

        Returns: str: The extracted price as a string.

        """
        for tag in soup(['script', 'style', 'noscript', 'iframe',
                         'head', 'footer', 'nav', 'del', 'header', 'a', 'ol', 'ul', 'li']):
            tag.decompose() # Remove unnecessary tags from the soup object

        # Get all elements with 'div', 'span', or 'p' tags
        all_elements = soup.find_all(['div', 'span', 'p'], recursive=True)
        # Iterate through all elements to find the price
        for element in all_elements:
            if isinstance(element, Tag):
                # Get text and clean it from extra spaces
                text = element.get_text().strip()


                # Check if the text is exactly a price format
                is_price = False
                for pattern in self.PRICE_PATTERNS:
                    if re.match(pattern, text):
                        is_price = True

                if is_price:
                    return element.get_text().strip()

    def get_title(self, soup):
        """
        Extract title from the given soup object.
        Args:
            soup:  The BeautifulSoup object representing the parsed HTML content.

        Returns: str: The extracted title as a string.

        """
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
                tag.decompose() # Remove unnecessary tags from the soup object

            for comment in soup.find_all(string=lambda text: isinstance(text, Comment)):
                comment.extract() # Remove comments from the soup object

            container = self._find_product_container(soup) # Find the main product container
            seen_title = container.find('h1').get_text(strip=True) # Extract title from the container

            return seen_title

        except Exception as e:
            print(f"Error extracting prices: {e}")
            return ""

    def extract_values(self, url: str, price_param: Optional[str] = None, descr_param: Optional[str] = None,
                       stock_param: Optional[str] = None) -> tuple[str | Any, str | Any, str | None, str | None]:
        """
        Extract values from the given URL using Playwright , BeautifulSoup and the patterns as parameters.
        Args:
            url: The URL of the page to extract information from
            price_param: The parameters for price extraction
            descr_param: The parameters for description extraction
            stock_param: The parameters for stock extraction

        Returns: tuple: A tuple containing the extracted price, title, description, and stock

        """
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=False) # Set headless to True for faster execution, but it's easily blocked by some sites
            page = browser.new_page() # Create a new page in the browser
            try:
                page.goto(url, timeout=30000) # Navigate to the URL with a timeout of 30 seconds
                page.wait_for_timeout(2000) # Wait for 2 seconds to allow the page to load
                html_content = page.content() # Get the HTML content of the page
            except Exception as e:
                print(f"Error loading page: {e}")
                return []
            finally:
                browser.close() # Close the browser after extraction

        soup = BeautifulSoup(html_content, 'lxml') # Parse the HTML content with BeautifulSoup for the description, title, stock and price (without attributes)extraction
        soup1 = BeautifulSoup(html_content, 'lxml') # Parse the HTML content with BeautifulSoup for the price extraction with get_price
        price = self.get_price(soup1) # Extract price
        title = self.get_title(soup) # Extract title
        description = '' # Initialize description
        stock = '' # Initialize stock
        # Extract price using the provided parameters
        if price_param:
            param_ = json.loads(price_param) # Load the price parameters
            attributes = json.loads(param_['attributes']) # Load the attributes for price extraction
            # Find elements with the specified tag and attributes
            if attributes:
                # Find elements with the specified tag and attributes
                element = soup.find(name=param_['tag'], attrs=attributes)
                # Extract the currency element from the meta tag if it exists
                currency_element = soup.find(name="meta", attrs={'property': 'product:price:currency'})
                # Check if the element has the 'content' attribute and the currency element is present
                if (element.has_attr('content') and currency_element):
                    # Format the price with commas and replace '.' with ','
                    price = f"{float(element['content']):,.3f}".replace(",", " ").replace(".", ",")
                    # Append the currency to the price
                    price += " " + currency_element['content']
                else:
                    price = element.get_text().strip()
            else:
                # Find elements without any attributes
                all_prices = soup1.find_all(lambda tag: tag.name == param_['tag'] and not tag.attrs)
                # Iterate through all elements to find the price
                for element in all_prices:
                    if (isinstance(element, Tag)):
                        text = element.get_text()
                        for pattern in self.PRICE_PATTERNS:
                            if re.match(pattern, text):
                                price = element.get_text().strip()
                                break
        # Extract description using the provided parameters
        if descr_param:
            descr_param_ = json.loads(descr_param)# Load the description parameters
            attributes = json.loads(descr_param_['attributes'])# Load the attributes for description extraction
            element = soup.find(name=descr_param_['tag'], attrs=attributes)# Find elements with the specified tag and attributes
            if (element.has_attr('content')):
                description = element['content'] # Extract the content attribute if it exists
            else:
                description = element.get_text()# Extract the text content if the content attribute does not exist
        # Extract stock using the provided parameters
        if stock_param:
            stock_param_ = json.loads(stock_param)# Load the stock parameters
            print(stock_param_)
            attributes = json.loads(stock_param_['attributes'])# Load the attributes for stock extraction
            element = soup.find(name=stock_param_['tag'], attrs=attributes)# Find elements with the specified tag and attributes
            if (element.has_attr('content')):
                stock = element['content']# Extract the content attribute if it exists
            else:
                stock = element.get_text() # Extract the text content if the content attribute does not exist

        return price, title, description, stock



# Usage
if __name__ == "__main__":
    extractor = DOMExtractor()
    url = "https://www.mytek.tn/trottinette-electrique-kepow-e9pro10s-noir.html"
    param = json.dumps({"tag":"meta","attributes":"{\"itemprop\":[\"price\"]}"})
    descr_param = json.dumps({"tag":"meta","attributes":"{\"property\":\"og:description\"}"})
    stock_param = json.dumps({"tag":"div","attributes":"{\"itemprop\":\"availability\"}"})

    prices,title,param,stock = extractor.extract_values(url, param=param, descr_param=descr_param)
    print(f"Found title: {title}\nFound prices: {prices}\nFound description: {param}\nFound stock: {stock}")