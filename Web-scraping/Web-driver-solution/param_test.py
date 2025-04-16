from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup, Comment ,Tag
import re

def test_method():
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=False)
        page = browser.new_page()
        try:
            page.goto("https://www.mytek.tn/trottinette-electrique-kepow-e9pro10s-noir.html", timeout=30000)
            page.wait_for_timeout(2000)
            html_content = page.content()
        except Exception as e:
            print(f"Error loading page: {e}")
            return []
        finally:
            browser.close()

    soup = BeautifulSoup(html_content, 'lxml')
    for tag in soup(['script', 'style', 'noscript', 'iframe',
                      'head', 'footer', 'nav', 'del', 'header', 'a', 'ol', 'ul', 'li']):
        tag.decompose()
    # List to store all found prices
    for tag in soup(['script', 'style', 'noscript', 'iframe']):
        tag.decompose()

    return soup

if __name__ == "__main__":
    print(test_method())