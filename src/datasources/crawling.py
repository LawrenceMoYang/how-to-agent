import json
import os

import requests
from bs4 import BeautifulSoup

from src.config import CONTENT_PATH, SRC_URL_FOR_SELLER_HOWTO
from src.datasources.html_utils import extract_text_from_html


def ebay_crawl(url: str, keyword: str, target_dir: str):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
    crawled_links = set()  # Set to keep track of crawled URLs

    try:
        # Send a request to get the HTML content of the page
        response = requests.get(url, headers=headers, timeout=10, verify=False)
        response.raise_for_status()  # Ensure we get a valid response
        soup = BeautifulSoup(response.text, 'html.parser')

        # Find all links containing the keyword
        links = [a['href'] for a in soup.find_all('a', href=True) if keyword in a['href']]

        # Create the target directory if it doesn't exist
        if not os.path.exists(target_dir):
            os.makedirs(target_dir)

        # List to hold JSON data for all crawled links
        json_data = []

        for link in links:
            # Check if link is already absolute
            if not link.startswith("http"):
                link = "https://www.ebay.com/" + link.lstrip('/')

            # Check if link has been crawled already
            if link in crawled_links:
                print(f"Skipped (already crawled): {link}")
                continue

            # Download the content of each link
            try:
                file_response = requests.get(link, headers=headers, timeout=10)
                file_response.raise_for_status()
                content = extract_text_from_html(file_response.text)

                # Add content and URL to JSON data
                json_data.append({
                    "url": link,
                    "content": content # Save content as text for JSON compatibility
                })

                print(f"Downloaded: {link}")
                crawled_links.add(link)  # Mark this link as crawled

            except requests.exceptions.RequestException as e:
                print(f"Failed to download {link}: {e}")

        # Write the JSON data to a file
        json_file_path = os.path.join(target_dir, keyword + "_" + "crawled_data.json")

        with open(json_file_path, 'w', encoding='utf-8') as json_file:
            json.dump(json_data, json_file, ensure_ascii=False, indent=4)

        print(f"Data saved to JSON file: {json_file_path}")

    except requests.exceptions.RequestException as e:
        print(f"Failed to retrieve the main page: {e}")




if __name__ == "__main__":
    ebay_crawl(url=SRC_URL_FOR_SELLER_HOWTO, keyword="sellercenter", target_dir=CONTENT_PATH)
