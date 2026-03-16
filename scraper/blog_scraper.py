from newspaper import Article
from langdetect import detect

def scrape_blog(url):

    article = Article(url)

    article.download()
    article.parse()

    title = article.title
    authors = article.authors
    publish_date = article.publish_date
    text = article.text

    paragraphs = text.split("\n")

    language = "unknown"
    try:
        language = detect(text)
    except:
        pass

    data = {
        "source_url": url,
        "source_type": "blog",
        "author": ", ".join(authors) if authors else "",
        "published_date": str(publish_date) if publish_date else "",
        "language": language,
        "region": "",
        "topic_tags": [],
        "trust_score": "",
        "content_chunks": paragraphs
    }

    return data
