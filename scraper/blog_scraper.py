import requests
from bs4 import BeautifulSoup
from langdetect import detect

def scrape_blog(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")

    # Title
    title = soup.title.text if soup.title else ""

    # Author
    author = ""
    author_tag = soup.find("meta", {"name": "author"})
    if author_tag:
        author = author_tag.get("content")

    # Published date
    published_date = ""
    date_tag = soup.find("meta", {"property": "article:published_time"})
    if date_tag:
        published_date = date_tag.get("content")

    # Extract paragraphs
    paragraphs = soup.find_all("p")
    content = [p.get_text() for p in paragraphs if len(p.get_text()) > 50]

    full_text = " ".join(content)

    # Language detection
    try:
        language = detect(full_text)
    except:
        language = "unknown"

    data = {
        "source_url": url,
        "source_type": "blog",
        "author": author,
        "published_date": published_date,
        "language": language,
        "region": "",
        "topic_tags": [],
        "trust_score": "",
        "content_chunks": content
    }

    return data
