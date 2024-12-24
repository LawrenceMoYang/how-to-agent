from bs4 import BeautifulSoup

def extract_text_from_html(html_text):
    """Extracts only relevant text content from an HTML filtering out links, tags, and other non-essential elements."""
    soup = BeautifulSoup(html_text, 'html.parser')

    # Remove unnecessary elements (e.g., scripts, styles, navigation links)
    for element in soup(['script', 'style', 'nav', 'footer', 'header', 'aside', 'form', 'noscript']):
        element.extract()

    # Extract text from main content tags
    content = []

    for tag in soup.find_all(['h1', 'h2', 'h3', 'p', 'li']):
        text = tag.get_text(separator=" ", strip=True)
        if text:  # Only add non-empty text
            content.append(text)

    # Join the extracted text with line breaks for readability
    relevant_text = "\n".join(content)

    return relevant_text