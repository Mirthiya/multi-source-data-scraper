import requests
from bs4 import BeautifulSoup

def scrape_pubmed(pmid):

    url = f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"

    r = requests.get(url)

    soup = BeautifulSoup(r.text,"html.parser")

    title = soup.find("h1").text.strip()

    authors = [a.text for a in soup.select(".authors-list .full-name")]

    abstract = soup.find("div", class_="abstract-content")

    text = abstract.text.strip() if abstract else ""

    chunks = text.split(".")

    return {
        "source_url": url,
        "source_type": "pubmed",
        "author": ", ".join(authors),
        "published_date": "",
        "language": "en",
        "region": "",
        "topic_tags": [],
        "trust_score": "",
        "content_chunks": chunks
    }
