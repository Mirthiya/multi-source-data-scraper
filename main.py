import json
from scraper.blog_scraper import scrape_blog
from scraper.youtube_scraper import scrape_youtube
from scraper.pubmed_scraper import scrape_pubmed
from utils.tagging import extract_topics
from utils.chunking import chunk_text
from scoring.trust_score import calculate_trust_score

data = []

# Example blog sources
blogs = [
    "https://towardsdatascience.com/",
    "https://machinelearningmastery.com/",
    "https://ai.googleblog.com/"
]

for blog in blogs:
    try:
        result = scrape_blog(blog)
        data.append(result)
    except:
        pass

# YouTube videos
videos = [
    "dQw4w9WgXcQ",
    "3fumBcKC6RE"
]

for vid in videos:
    try:
        result = scrape_youtube(vid)
        data.append(result)
    except:
        pass

# PubMed article
pubmed_id = "31452104"

try:
    result = scrape_pubmed(pubmed_id)
    data.append(result)
except:
    pass


with open("output/scraped_data.json", "w") as f:
    json.dump(data, f, indent=4)

print("Scraping completed.")
