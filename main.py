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
    "https://machinelearningmastery.com/",
    "https://towardsdatascience.com/",
    "https://ai.googleblog.com/"
]

for blog in blogs:
    try:
        result = scrape_blog(blog)
        data.append(result)
    except:
        pass


# YouTube sources
videos = [
    "3fumBcKC6RE",
    "dQw4w9WgXcQ"
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

    # topic tagging
    if item["content_chunks"]:
        item["topic_tags"] = extract_topics(item["content_chunks"])
    else:
        item["topic_tags"] = []

    # chunking
    if item["content_chunks"]:
        item["content_chunks"] = chunk_text(item["content_chunks"])

    # trust score
    item["trust_score"] = calculate_trust_score(
        item["author"],
        citations=20,
        domain=item["source_url"],
        year=2022,
        disclaimer=False
    )


# Save JSON
with open("output/scraped_data.json", "w") as f:
    json.dump(data, f, indent=4)

print("Scraping completed.")
