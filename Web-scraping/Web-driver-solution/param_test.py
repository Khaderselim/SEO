from playwright.sync_api import sync_playwright
import json

def test_proxy_connection():
    with sync_playwright() as playwright:
        try:
            browser = playwright.chromium.launch(
                proxy={
                    "server": "socks5://127.0.0.1:8899",
                    "bypass": "127.0.0.1"
                },
                headless=False
            )
            context = browser.new_context(ignore_https_errors=True)
            page = context.new_page()

            # Test the proxy connection with a simple request
            page.goto("https://api.ipify.org?format=json", timeout=30000)
            ip_info = page.evaluate("() => document.body.textContent")
            print(f"Proxy IP: {ip_info}")

            browser.close()
            return True
        except Exception as e:
            print(f"Proxy connection error: {e}")
            return False

def test_method():
    if not test_proxy_connection():
        return "Proxy connection failed"

    with sync_playwright() as playwright:
        try:
            browser = playwright.chromium.launch(
                proxy={
                    "server": "socks5://127.0.0.1:8899",
                    "bypass": "127.0.0.1"
                },
                headless=False
            )
            context = browser.new_context(ignore_https_errors=True)
            page = context.new_page()
            page.goto("https://mytek.tn/", timeout=30000)
            content = page.content()
            browser.close()
            return content
        except Exception as e:
            print(f"Error: {e}")
            return str(e)

if __name__ == "__main__":
    result = test_method()
    print(result)