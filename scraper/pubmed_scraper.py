import requests
from bs4 import BeautifulSoup

def scrape_pubmed(pmid):

    url = f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"
    response = requests.get(url)

    soup = BeautifulSoup(response.text, "html.parser")

    title = ""
    title_tag = soup.find("h1")
    if title_tag:
        title = title_tag.text.strip()

    authors = []
    author_tags = soup.find_all("a", class_="full-name")
    for a in author_tags:
        authors.append(a.text.strip())

    abstract = ""
    abstract_tag = soup.find("div", class_="abstract-content")
    if abstract_tag:
        abstract = abstract_tag.text.strip()

    content_chunks = abstract.split(".")

    data = {
        "source_url": url,
        "source_type": "pubmed",
        "author": ", ".join(authors),
        "published_date": "",
        "language": "en",
        "region": "",
        "topic_tags": [],
        "trust_score": "",
        "content_chunks": content_chunks
    }

    return data
