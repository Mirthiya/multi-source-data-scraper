import json
from scraper.blog_scraper import scrape_blog
from scraper.youtube_scraper import scrape_youtube
from scraper.pubmed_scraper import scrape_pubmed

from utils.tagging import extract_topics
from utils.chunking import chunk_text
from scoring.trust_score import calculate_trust_score

data = []

# Blog sources
blogs = [
"https://machinelearningmastery.com/what-is-machine-learning/",
"https://machinelearningmastery.com/5-tips-for-getting-started-with-deep-learning/",
"https://machinelearningmastery.com/a-gentle-introduction-to-the-challenge-of-training-deep-learning-neural-network-models/"
]

for blog in blogs:
    try:
        result = scrape_blog(blog)
        data.append(result)
    except:
        pass


# YouTube sources
videos = [
"https://youtube.com/watch?v=aircAruvnKk",
"https://youtube.com/watch?v=kCc8FmEb1nY"
]

for vid in videos:
    try:
        result = scrape_youtube(vid)
        data.append(result)
    except:
        pass


# PubMed source
try:
    result = scrape_pubmed("31452104")
    data.append(result)
except:
    pass


for item in data:

    # Safety check for content
    content = item.get("content_chunks", [])

    if content and len(content) > 0:
        item["topic_tags"] = extract_topics(content)
        item["content_chunks"] = chunk_text(content)
    else:
        item["topic_tags"] = []
        item["content_chunks"] = []

    # Calculate trust score
    item["trust_score"] = calculate_trust_score(
        item.get("author", ""),
        citations=20,
        domain=item.get("source_url", ""),
        year=2022,
        disclaimer=False
    )


# Save JSON
with open("output/scraped_data.json", "w") as f:
    json.dump(data, f, indent=4)

print("Scraping completed.")
