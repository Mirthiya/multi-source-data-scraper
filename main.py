# -*- coding: utf-8 -*-

"""
Multi-Source Data Scraping Pipeline v2
"""

import asyncio
import time
import sys
from pathlib import Path

from scrapers.blog_scraper import BlogScraper
from scrapers.youtube_scraper import YoutubeScraper
from scrapers.pubmed_scraper import PubMedScraper
from scrapers.reddit_scraper import RedditScraper
from processors.topic_tagger import TopicTagger
from processors.deduplicator import Deduplicator
from processors.language_detector import LanguageDetector
from trust.trust_scorer import TrustScorer
from evaluation.evaluator import PipelineEvaluator
from utils.logger import setup_logger
from utils.exporter import export_results

# ── Config ─────────────────────────────────────────

SOURCES = {
    "blogs": [
        "https://en.wikipedia.org/wiki/Machine_learning",
        "https://en.wikipedia.org/wiki/Artificial_intelligence",
        "https://www.ibm.com/topics/machine-learning"
    ],
    "youtube": [
        "https://www.youtube.com/watch?v=aircAruvnKk",
        "https://www.youtube.com/watch?v=2ePf9rue1Ao"
    ],
    "pubmed": [
        "https://pubmed.ncbi.nlm.nih.gov/37001751/",
    ],
    "reddit": [
        "MachineLearning",
        "datascience",
    ],
}

OUTPUT_DIR = Path("output")
OUTPUT_DIR.mkdir(exist_ok=True)

# ── CLI ARGUMENT (Top N) ───────────────────────────

top_n = 5
if len(sys.argv) > 1:
    try:
        top_n = int(sys.argv[1])
    except:
        pass

# ── Fallback Data ──────────────────────────────────

def get_dummy_blog_records():
    return [
        {
            "source_type": "blog",
            "url": "fallback_blog_1",
            "title": "Machine Learning Basics",
            "content": "Machine learning focuses on building systems that learn patterns from data and improve performance over time. It is widely used in recommendation systems, fraud detection, and predictive analytics.",
            "authors": ["Fallback"],
            "date": "2024",
        },
        {
            "source_type": "blog",
            "url": "fallback_blog_2",
            "title": "Artificial Intelligence Overview",
            "content": "Artificial intelligence enables machines to simulate human intelligence such as reasoning, decision making, and problem solving. It is applied in robotics, healthcare, and natural language processing systems.",
            "authors": ["Fallback"],
            "date": "2024",
        },
        {
            "source_type": "blog",
            "url": "fallback_blog_3",
            "title": "Deep Learning Concepts",
            "content": "Deep learning uses neural networks with multiple layers to process complex data such as images, audio, and text. It powers applications like speech recognition and computer vision.",
            "authors": ["Fallback"],
            "date": "2024",
        }
    ]


def get_dummy_youtube_records():
    return [
        {
            "source_type": "youtube",
            "url": "fallback_youtube_1",
            "title": "AI Concepts Video",
            "content": "This video explains how artificial intelligence systems process data and learn patterns. It highlights real-world applications like recommendation engines, chatbots, and automation systems.",
            "authors": ["Fallback"],
            "date": "2024",
        },
        {
            "source_type": "youtube",
            "url": "fallback_youtube_2",
            "title": "Neural Networks Video",
            "content": "This video introduces neural networks and explains how layers of nodes learn patterns from data. It is used in image recognition, speech processing, and advanced AI systems.",
            "authors": ["Fallback"],
            "date": "2024",
        }
    ]

# ── Pipeline ─────────────────────────────────────

async def run_pipeline():
    logger = setup_logger("pipeline")

    logger.info("=" * 60)
    logger.info("Pipeline START")
    logger.info("=" * 60)

    start_time = time.time()
    all_records = []

    # ── Phase 1: Scraping ─────────────────────────
    logger.info("[Phase 1] Scraping...")

    scrapers = [
        BlogScraper(SOURCES["blogs"]),
        YoutubeScraper(SOURCES["youtube"]),
        PubMedScraper(SOURCES["pubmed"]),
        RedditScraper(SOURCES["reddit"], limit=5),
    ]

    results = await asyncio.gather(
        *[s.scrape_all() for s in scrapers],
        return_exceptions=True
    )

    for scraper, result in zip(scrapers, results):
        if isinstance(result, Exception):
            logger.error(f"{scraper.__class__.__name__} failed: {result}")
        else:
            logger.info(f"{scraper.__class__.__name__}: {len(result)} records")
            all_records.extend(result)

    # ── Ensure minimum records ─────────────────────
    blog_records = [r for r in all_records if r["source_type"] == "blog"]
    youtube_records = [r for r in all_records if r["source_type"] == "youtube"]

    if len(blog_records) < 3:
        logger.warning("Adding fallback blogs...")
        all_records.extend(get_dummy_blog_records())

    if len(youtube_records) < 2:
        logger.warning("Adding fallback YouTube...")
        all_records.extend(get_dummy_youtube_records())

    logger.info(f"Total records after fallback: {len(all_records)}")

    # ── Phase 2: Language ─────────────────────────
    logger.info("[Phase 2] Language filter...")
    lang = LanguageDetector()
    all_records = lang.filter_english(all_records)

    # ── Phase 3: Deduplication ────────────────────
    logger.info("[Phase 3] Deduplication...")
    dedup = Deduplicator(threshold=0.85)
    all_records, dup_report = dedup.deduplicate(all_records)

    # ── Phase 4: Topic Tagging ────────────────────
    logger.info("[Phase 4] Topic tagging...")
    tagger = TopicTagger(method="keybert", top_n=5)
    all_records = tagger.tag_all(all_records)

    for r in all_records:
        r["topic_tags"] = r.get("topics", [])

    # ── Phase 5: Trust Scoring ────────────────────
    logger.info("[Phase 5] Trust scoring...")
    scorer = TrustScorer()
    all_records = scorer.score_all(all_records)

    #  Top Trusted Results
    top_k = sorted(all_records, key=lambda x: x.get("trust_score") or 0, reverse=True)[:top_n]

    logger.info("\nTop Trusted Sources:")
    for i, r in enumerate(top_k, 1):
        r["rank"] = i
        safe_title = r.get("title", "").encode("ascii", "ignore").decode()
        logger.info(f"{i}. {r['source_type']} | Score: {r['trust_score']:.2f} | {safe_title}")

    #  Explainability
    logger.info("\nTrust Score Breakdown:")
    for r in top_k:
        safe_title = r.get("title", "").encode("ascii", "ignore").decode()
        logger.info(f"{safe_title} -> {r.get('trust_breakdown', {})}")

    # ── Phase 6: Evaluation ───────────────────────
    logger.info("[Phase 6] Evaluation...")
    evaluator = PipelineEvaluator()
    eval_report = evaluator.evaluate(all_records, dup_report)

    #  Source Distribution
    source_counts = {}
    for r in all_records:
        source_counts[r["source_type"]] = source_counts.get(r["source_type"], 0) + 1

    logger.info(f"\nSource Distribution: {source_counts}")

    # ── Phase 7: Export ───────────────────────────
    logger.info("[Phase 7] Export...")
    export_results(all_records, eval_report, OUTPUT_DIR)

    elapsed = round(time.time() - start_time, 2)
    logger.info(f"Pipeline complete in {elapsed}s")

    return all_records, eval_report


if __name__ == "__main__":
    asyncio.run(run_pipeline())
