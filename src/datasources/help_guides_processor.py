import json
from tqdm import tqdm
from src.config import HELP_GUIDES_RAW_PATH, CONTENT_PATH
from src.datasources.html_utils import extract_text_from_html


def guides_processor(guides_path: str, target_dir: str):

    try:
        with open(guides_path, 'r') as json_file:
            data = json.load(json_file)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error reading JSON file: {e}")
        return

    try:
        data = [{item['name'].split("HELP.")[1]: item['value'] for item in content['contentData']} for content
                              in data['contentDetails']]
    except KeyError as e:
        print(f"Error processing data: {e}")
        return

    docs = []
    for idx, webpage in tqdm(enumerate(data), total=len(data), desc="Processing help guides"):
        if {'TITLE', 'ARTICLE_DESCRIPTION', 'PAGE_URL', 'DESKTOP_BODY'}.issubset(webpage):
            docs.append({
                "url": f"https://www.ebay.com{webpage['PAGE_URL']}",
                "content": (
                    f"Help webpage title: {webpage['TITLE']} \n"
                    f"Help webpage description: {extract_text_from_html(webpage['ARTICLE_DESCRIPTION'])} \n"
                    f"Help webpage content: {extract_text_from_html(webpage['DESKTOP_BODY'])}"
                )
            })

    print(f"Collected {len(docs)} help guides")

    try:
        with open(f"{target_dir}/help_guides_data.json", 'w', encoding='utf-8') as json_file:
            json.dump(docs, json_file, ensure_ascii=False, indent=4)
    except IOError as e:
        print(f"Error writing JSON file: {e}")


if __name__ == "__main__":
    guides_processor(guides_path=HELP_GUIDES_RAW_PATH, target_dir=CONTENT_PATH)