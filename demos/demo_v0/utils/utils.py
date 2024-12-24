import base64
import getpass
import os
import time
import requests
from PIL import Image
import io


def fetch_proxies(yubi_user=None, yubi_key=None):
    """Fetch the proxies for an API call."""
    
    if not yubi_user:
        yubi_user = getpass.getuser()
    
    if not yubi_key:
        yubi_key = os.getenv('YUBIKEY', "")

    proxies = {}
    if yubi_key and yubi_user:
        proxies = {
            "http": f"http://{yubi_user}:{yubi_key}@c2sproxy.vip.ebay.com:8080",
            "https": f"http://{yubi_user}:{yubi_key}@c2sproxy.vip.ebay.com:8080",
        }

    return proxies

def is_production_connected(proxies=None):
    url = "http://modelengineservice.vip.ebay.com/actuator/health"


    try:
        r = requests.head(url=url, headers=None, proxies=proxies, verify=False, timeout=100)

        if r.status_code == 200:
            return True
        else:
            return False
    except requests.RequestException as e:
        return False

def fetch(username, pin_and_yubikey, url):
    """Function to send a GET request to the provided URL."""
    print("yubi_key")
    return requests.get(url, verify=False, timeout=2, proxies=fetch_proxies(username, pin_and_yubikey))


def fetch_token():
    token = os.getenv("IAF_TOKEN")
    return token


def get_headers(json=True, token=None):
    """Get the headers for an API call."""
    if token is None:
        token = os.getenv("IAF_TOKEN")

    return {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json' if json else "text/plain",
        'Accept': 'application/json'
    }


def call_ebay_service(url, body=None, data=None, yubi_user=None, yubi_key=None, bearer_token=None):
    """Call an eBay service with the given URL and body."""
    assert bool(body) ^ bool(data)
    proxies = fetch_proxies(yubi_user, yubi_key)
    headers = get_headers(bool(body), bearer_token)
    r = requests.post(url, headers=headers, json=body, data=data, proxies=proxies, verify=False)

    if r.status_code == 200:
        return r.json()
    else:
        print(f"Unexpected status code: {r.status_code}")
        # Optionally, return or log the error for further handling
        return None


def recs_list_to_markdown(recs: list) -> str:
    template = """
{index}. **[{title}]({url})**
- Price: ${price:.2f}
- Condition: {condition}
{aspects_list}
- ![Image]({image_url})
"""

    aspects_template = "- {name}: {value}"

    item_strs = []

    for i, rec in enumerate(recs):
        if 'title' not in rec:
            print('!!!!!!!!!!Title not found for some reason!!!!!!!!!!!!')
            print(rec)
        aspects_list = ''
        item_strs.append(
            template.format(
                index=i + 1,
                title=rec.get('title', ""),
                url=f"https://www.ebay.com/itm/{rec['listingId']}",
                price=rec.get('price', ""),
                condition=rec.get('condition', ""),
                aspects_list=aspects_list,
                image_url=rec.get('imageUrl', "")
            )
        )

    return '\n\n'.join(item_strs)


def image_to_base64(image: Image) -> str:
    buffer = io.BytesIO()
    image.convert('RGB').save(buffer, format="jpeg")
    payload = base64.b64encode(buffer.getvalue()).decode("utf-8")
    return payload


def resize_image(image, max_side):
    """
    Resize the image so that the maximum side is `max_side` pixels,
    maintaining the aspect ratio.
    """
    # Calculate the scaling factor, keeping the aspect ratio
    ratio = min(max_side / image.width, max_side / image.height)
    new_width = int(image.width * ratio)
    new_height = int(image.height * ratio)

    # Resize the image
    resized_image = image.resize((new_width, new_height))
    return resized_image


def time_logger(func):
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        print(f"{func.__name__} executed in {end_time - start_time} seconds")
        return result
    return wrapper


@time_logger
def download_image(image_url: str, size=None) -> Image:
    """Downloads a remote image into memory."""

    # Proxies in case we are in prod env
    proxies = {}
    local_proxies = fetch_proxies()
    if not local_proxies:
        proxies = {
            'http': 'http://httpproxy-tcop.vip.ebay.com:80',
            'https': 'http://httpproxy-tcop.vip.ebay.com:80',
        }
    response = requests.get(
        image_url,
        proxies=proxies
    )
    image = Image.open(io.BytesIO(response.content))
    if size:
        image = image.resize(size)
    return image


if __name__ == "__main__":
    a = [
        {
            "listingId": 295372114421,
            "title": "Adjustable Running hat",
            "currency": "USD",
            "price": 12.99,
            "format": "FixedPrice",
            "listingUrl": "https://www.ebay.com/itm/295372114421",
            "imageUrl": "https://i.ebayimg.com/images/g/3HoAAOSwqEZjg8HT/s-l225.jpg",
            "categoryId": 52365,
            "aspects": {
                "features": [
                    "lightweight",
                    "adjustable"
                ],
                "color": [
                    "red"
                ],
                "season": [
                    "summer",
                    "fall",
                    "spring"
                ],
                "country/region of manufacture": [
                    "china"
                ],
                "material": [
                    "polyester"
                ]
            },
            "marketplace": "EBAY-US",
            "condition": 1000
        },
        {
            "listingId": 356048261422,
            "title": "Cooling Sprint Hat, - Unisex Running Hat for Men & Women - Lightweight, Flexi...",
            "currency": "USD",
            "price": 28.560000000000002,
            "format": "FixedPrice",
            "listingUrl": "https://www.ebay.com/itm/356048261422",
            "imageUrl": "https://i.ebayimg.com/images/g/7iAAAOSwGhxm5qEZ/s-l225.jpg",
            "categoryId": 52365,
            "aspects": {
                "model": [
                    "sprint hat"
                ],
                "style": [
                    "golf hat"
                ],
                "features": [
                    "stretch",
                    "uv protection",
                    "breathable",
                    "lightweight",
                    "adjustable",
                    "quick dry"
                ],
                "brand": [
                    "mission"
                ],
                "department": [
                    "men"
                ],
                "material": [
                    "polyester",
                    "spandex",
                    "nylon"
                ],
                "occasion": [
                    "travel",
                    "casual",
                    "formal"
                ],
            },
            "marketplace": "EBAY-US",
            "condition": 1000
        },
    ]
    print(recs_list_to_markdown(a))