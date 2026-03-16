import requests

def scrape_pubmed(url):
    response = requests.get(url)
    data = response.text

    return {
        "source_url": url,
        "source_type": "pubmed",
        "content": data
    }