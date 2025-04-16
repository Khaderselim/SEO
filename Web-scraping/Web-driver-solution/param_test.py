from playwright.sync_api import sync_playwright
import json

def test_proxy_connection():
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            proxy={
                "server": "socks5://127.0.0.1:8899",
            },
            headless=True
        )
        try:
            context = browser.new_context(ignore_https_errors=True)
            page = context.new_page()
            page.goto("https://api.ipify.org?format=json")
            content = page.content()
            print(f"IP Check: {content}")
            return True
        except Exception as e:
            print(f"Proxy Error: {e}")
            return False
        finally:
            browser.close()

def test_method():
    if not test_proxy_connection():
        return "Proxy connection failed"

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            proxy={
                "server": "socks5://127.0.0.1:8899",
            },
            headless=True
        )
        try:
            context = browser.new_context(ignore_https_errors=True)
            page = context.new_page()
            page.goto("https://www.mytek.tn/trottinette-electrique-kepow-e9pro10s-noir.html", timeout=30000)
            return page.content()
        except Exception as e:
            print(f"Error: {e}")
            return str(e)
        finally:
            browser.close()

if __name__ == "__main__":
    print(test_method())