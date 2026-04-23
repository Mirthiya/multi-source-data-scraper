"""
Reddit Scraper
==============
Adds a 4th data source: Reddit discussion threads.
Uses Reddit's public JSON API (no auth required for public subreddits).

Captures: post title, selftext, top comments, upvote ratio,
author, subreddit, post date, flair.

This source adds:
  - Community-validated content (upvote signal)
  - Real-time discussion and expert commentary
  - Diverse topics not covered by academic sources
"""

import asyncio
import logging
from typing import Optional
from datetime import datetime, timezone

from scrapers.base_scraper import BaseScraper, make_record

logger = logging.getLogger(__name__)

REDDIT_JSON = "https://www.reddit.com/r/{subreddit}/hot.json?limit={limit}"
POST_JSON = "https://www.reddit.com/r/{subreddit}/comments/{post_id}.json?limit=10"

# Subreddits with high signal-to-noise ratio
HIGH_QUALITY_SUBREDDITS = {
    "MachineLearning", "datascience", "learnmachinelearning",
    "statistics", "artificial", "deeplearning",
}


class RedditScraper(BaseScraper):
    """
    Async Reddit scraper using public JSON API.
    No authentication required. Respects Reddit rate limits.
    Extracts post + top comments as unified content.
    """

    RATE_LIMIT_DELAY = 2.0  # Reddit is stricter: 2s between requests

    def __init__(self, subreddits: list[str], limit: int = 5):
        super().__init__()
        self.subreddits = subreddits
        self.limit = limit
        self._headers = {
            **self._headers,
            "Accept": "application/json",
        }

    def _get_targets(self) -> list[str]:
        # Targets are subreddit names; scrape_one fetches multiple posts
        return self.subreddits

    async def scrape_all(self) -> list[dict]:
        """Override: each target returns multiple records."""
        all_records = []
        for subreddit in self.subreddits:
            await self._rate_limit(f"reddit.com/{subreddit}")
            records = await self._scrape_subreddit(subreddit)
            all_records.extend(records)
            logger.debug(f"RedditScraper: {len(records)} posts from r/{subreddit}")
        return all_records

    async def scrape_one(self, target: str) -> Optional[dict]:
        # Not used directly; scrape_all is overridden
        return None

    # ── Subreddit Scraping ─────────────────────────────────────────────────────

    async def _scrape_subreddit(self, subreddit: str) -> list[dict]:
        url = REDDIT_JSON.format(subreddit=subreddit, limit=self.limit)
        try:
            response = await self._fetch(url)
            response.raise_for_status()
            data = response.json()
        except Exception as e:
            logger.warning(f"RedditScraper: failed to fetch r/{subreddit}: {e}")
            return []

        posts = data.get("data", {}).get("children", [])
        records = []

        for post_data in posts:
            post = post_data.get("data", {})
            record = await self._process_post(post, subreddit)
            if record:
                records.append(record)

        return records

    async def _process_post(self, post: dict, subreddit: str) -> Optional[dict]:
        title = post.get("title", "").strip()
        selftext = post.get("selftext", "").strip()
        post_id = post.get("id", "")
        author = post.get("author", "[deleted]")
        score = post.get("score", 0)
        upvote_ratio = post.get("upvote_ratio", 0.5)
        flair = post.get("link_flair_text", "")
        created_utc = post.get("created_utc", 0)

        # Skip deleted / low-quality posts
        if not title or author == "[deleted]":
            return None
        if selftext in ("[deleted]", "[removed]", ""):
            selftext = ""

        # Fetch top comments for richer content
        comments = await self._fetch_top_comments(post_id, subreddit)

        # Combine selftext + top comments
        content_parts = [title]
        if selftext:
            content_parts.append(selftext)
        if comments:
            content_parts.append("Top community responses: " + " | ".join(comments[:3]))

        content = " ".join(content_parts)

        if len(content.split()) < 20:
            return None

        post_date = datetime.fromtimestamp(created_utc, tz=timezone.utc).strftime("%Y-%m-%d") \
            if created_utc else ""

        post_url = f"https://www.reddit.com/r/{subreddit}/comments/{post_id}/"

        return make_record(
            source_type="reddit",
            url=post_url,
            title=title,
            content=content,
            authors=[author],
            date=post_date,
            extra={
                "subreddit": subreddit,
                "reddit_score": score,
                "upvote_ratio": upvote_ratio,
                "flair": flair,
                "is_trusted_domain": subreddit in HIGH_QUALITY_SUBREDDITS,
                "has_citations": any(kw in content.lower() for kw in ["paper", "doi", "arxiv", "study"]),
                "has_disclaimer": "opinion" in content.lower(),
                "community_validated": upvote_ratio > 0.85 and score > 50,
            },
        )

    async def _fetch_top_comments(self, post_id: str, subreddit: str) -> list[str]:
        """Fetch top 3 comments for a post."""
        url = POST_JSON.format(subreddit=subreddit, post_id=post_id)
        try:
            await asyncio.sleep(0.5)  # gentle pacing for comment fetch
            response = await self._fetch(url)
            response.raise_for_status()
            data = response.json()

            if not isinstance(data, list) or len(data) < 2:
                return []

            comments_data = data[1].get("data", {}).get("children", [])
            comments = []
            for c in comments_data[:5]:
                body = c.get("data", {}).get("body", "").strip()
                if body and body not in ("[deleted]", "[removed]") and len(body) > 20:
                    comments.append(body[:300])
            return comments
        except Exception:
            return []
