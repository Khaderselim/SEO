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


def extract_prices(url: str):
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
    for tag in soup(['script', 'style', 'noscript', 'iframe',
                     'meta', 'head', 'footer', 'nav', 'del', 'header', 'a', 'ol', 'ul', 'li']):
        tag.decompose()
    # Dictionary to store unique prices (key: normalized price, value: best tag)
    price_dict = {}

    # Get all elements
    all_elements = soup.find_all(['div','span','p'], recursive=True)

    for element in all_elements:
        if isinstance(element, Tag):
            # Get text and clean it
            text = element.get_text().strip()

            # Skip empty text or extremely long text (likely containers)


            # Check if the text is exactly a price format
            is_price = False
            for pattern in PRICE_PATTERNS:
                if re.match(pattern, text):
                    is_price = True


            if is_price:
                # Normalize the price (remove spaces, use period as decimal)
                normalized = re.sub(r'\s', '', text)
                normalized = re.sub(r',', '.', normalized)

                # If we haven't seen this price before, or the current element has attributes
                # and the stored one doesn't, update our dictionary
                if element.attrs:
                    price_dict[normalized] = element

    # Convert dictionary to list of results
    results = []
    for price, element in price_dict.items():
        results.append({
            'price': element.get_text().strip(),
            'tag_name': element.name,
            'attributes': element.attrs
        })

    return results


urls = [
    "https://www.mytek.tn/pc-de-bureau-gamer-mytek-amd-ryzen-5-16go-zotac-rtx-3060-twin-edge-12go.html",
    "https://www.tunisianet.com.tn/smartphone-samsung/54775-smartphone-samsung-galaxy-a04e-noir-4g.html",
    "https://wiki.tn/hisense-43a5200f-televiseur-43-led-fhd/",
    "https://fnac.tn/product/casque-jbl-t520-bt-bleu-F10640721",
    "https://fnac.tn/product/casque-swingson-bt-black-F10640724",
    "https://www.zara.com/tn/fr/veste-droite-effet-daim-p02518907.html?v1=433327289&v2=2546081",
    "https://www.stradivarius.com/tn/trench-long-en-suedine-l01851683?categoryId=1020206021&colorId=440&style=03&pelement=446347584",
    "https://www.tunisianet.com.tn/refrigerateur-tunisie/72449-refrigerateur-samsung-rt31-305-litres-nofrost-silver-.html",
    "https://www.ebay.com/itm/166940209780?_trkparms=amclksrc%3DITM%26aid%3D777008%26algo%3DPERSONAL.TOPIC%26ao%3D1%26asc%3D20230906152218%26meid%3D6d366f2dd0b548a5b1e38b6f6ad6111f%26pid%3D101817%26rk%3D1%26rkt%3D1%26itm%3D166940209780%26pmt%3D0%26noa%3D1%26pg%3D4375194%26algv%3DPersonalizedTopicsV2WithSizeMsku%26brand%3DSeiko&_trksid=p4375194.c101817.m47269&_trkparms=parentrq%3A654a8b9c1950ab119b93eb1dffff85ca%7Cpageci%3Ac37bddfc-f996-11ef-965e-9275ce0d6854%7Ciid%3A1%7Cvlpname%3Avlp_homepage",
    "https://animalzone.tn/pack/4980-ownat-sterilized-15-kg-2-lindocat-charme-ambre-oriental-10l.html"
]
for url in urls:
    print(f"\nTesting URL: {url}")
    prices = extract_prices(url)
    if prices:
        print(f"Found {len(prices)} unique prices:")
        for i, item in enumerate(prices, 1):
            print(f"\n{i}. Price: {item['price']}")
            print(f"   Tag: {item['tag_name']}")
            print(f"   Attributes: {item['attributes']}")
    else:
        print("No prices found")

    #   Attributes: {'id': 'brxe-dgbbbm', 'class': ['brxe-product-price', 'product-card__price-new']}
