from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup

def test_method():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=50)

        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 720},
            locale="fr-FR",
            java_script_enabled=True,
        )

        page = context.new_page()
        try:
            page.goto("https://www.mytek.tn/trottinette-electrique-kepow-e9pro10s-noir.html", timeout=60000)
            page.wait_for_selector("body", timeout=10000)
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

    return soup

if __name__ == "__main__":
    print(test_method())
