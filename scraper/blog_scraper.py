import requests
from bs4 import BeautifulSoup

def scrape_blog(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")

    title = soup.title.text if soup.title else ""

    paragraphs = soup.find_all("p")
    content = [p.get_text() for p in paragraphs]

    data = {
        "source_url": url,
        "source_type": "blog",
        "title": title,
        "content": content
    }

    return data