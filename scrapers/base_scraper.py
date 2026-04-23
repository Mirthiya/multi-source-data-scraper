"""
Base Scraper
============
All scrapers inherit from this. Provides:
  - Async HTTP with httpx
  - Exponential backoff retry (3 attempts)
  - Per-domain rate limiting (1 req/sec default)
  - Structured record schema
  - Timeout handling
"""

import asyncio
import hashlib
import logging
import time
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional
import httpx

logger = logging.getLogger(__name__)

# ── Schema ─────────────────────────────────────────────────────────────────────

def make_record(
    source_type: str,
    url: str,
    title: str = "",
    content: str = "",
    authors: list = None,
    date: str = "",
    domain: str = "",
    extra: dict = None,
) -> dict:
    """
    Canonical data schema for every scraped record.
    All downstream processors expect this shape.
    """
    content_clean = content.strip()
    return {
    # Internal fields (your pipeline)
    "source_id": hashlib.md5(url.encode()).hexdigest()[:12],
    "source_type": source_type,
    "url": url,
    "domain": domain or _extract_domain(url),
    "title": title.strip(),
    "authors": authors or ["Unknown"],
    "date": date or datetime.utcnow().strftime("%Y-%m-%d"),
    "content": content_clean,
    "word_count": len(content_clean.split()),
    "topics": [],
    "trust_score": None,
    "trust_breakdown": {},
    "language": "unknown",
    "scrape_timestamp": datetime.utcnow().isoformat(),

    #  REQUIRED ASSIGNMENT FIELDS (IMPORTANT)
    "source_url": url,
    "author": author_value,
    "published_date": published_date,
    "region": region_value,
    "topic_tags": [],  # will be filled later
    "content_chunks": content_clean.split(".")[:5],  # simple chunking

    **(extra or {}),
}

def _extract_domain(url: str) -> str:
    try:
        from urllib.parse import urlparse
        return urlparse(url).netloc.replace("www.", "")
    except Exception:
        return ""


# ── Base Scraper ───────────────────────────────────────────────────────────────

class BaseScraper(ABC):
    """
    Abstract base scraper. Subclasses implement `scrape_one(url)`.
    Handles retries, rate limiting, and error isolation automatically.
    """

    MAX_RETRIES = 3
    BACKOFF_BASE = 2        # seconds (exponential: 2, 4, 8)
    RATE_LIMIT_DELAY = 1.0  # seconds between requests to same domain
    TIMEOUT = 15            # seconds

    def __init__(self):
        self._last_request_time: dict[str, float] = {}
        self._headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Connection": "keep-alive"
}

    # ── Public API ─────────────────────────────────────────────────────────────

    async def scrape_all(self) -> list[dict]:
        """Scrape all targets concurrently with semaphore (max 5 parallel)."""
        targets = self._get_targets()
        sem = asyncio.Semaphore(5)

        async def bounded(target):
            async with sem:
                return await self._scrape_with_retry(target)

        tasks = [bounded(t) for t in targets]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        records = []
        for i, r in enumerate(results):
            if isinstance(r, Exception):
                logger.warning(f"  [{self.__class__.__name__}] Failed {targets[i]}: {r}")
            elif r:
                records.append(r)
        return records

    # ── Internal ───────────────────────────────────────────────────────────────

    async def _scrape_with_retry(self, target: str) -> Optional[dict]:
        """Retry with exponential backoff on failure."""
        for attempt in range(1, self.MAX_RETRIES + 1):
            try:
                await self._rate_limit(target)
                record = await self.scrape_one(target)
                if record and record.get("word_count", 0) >= 30:
                    return record
                logger.debug(f"  [{self.__class__.__name__}] Skipped (too short): {target}")
                return None
            except (httpx.TimeoutException, httpx.NetworkError) as e:
                wait = self.BACKOFF_BASE ** attempt
                logger.warning(
                    f"  [{self.__class__.__name__}] Attempt {attempt}/{self.MAX_RETRIES} "
                    f"failed for {target}: {type(e).__name__}. Retrying in {wait}s..."
                )
                if attempt < self.MAX_RETRIES:
                    await asyncio.sleep(wait)
            except Exception as e:
                logger.error(f"  [{self.__class__.__name__}] Unrecoverable error {target}: {e}")
                return None
        logger.error(f"  [{self.__class__.__name__}] All retries exhausted for {target}")
        return None

    async def _rate_limit(self, target: str):
        """Enforce per-domain rate limiting."""
        domain = _extract_domain(target)
        now = time.monotonic()
        last = self._last_request_time.get(domain, 0)
        wait = self.RATE_LIMIT_DELAY - (now - last)
        if wait > 0:
            await asyncio.sleep(wait)
        self._last_request_time[domain] = time.monotonic()

    async def _fetch(self, url: str) -> httpx.Response:
        """Async HTTP GET with timeout."""
        async with httpx.AsyncClient(
            headers=self._headers,
            timeout=self.TIMEOUT,
            follow_redirects=True,
        ) as client:
            return await client.get(url)

    @abstractmethod
    def _get_targets(self) -> list[str]:
        """Return list of URLs / identifiers to scrape."""
        ...

    @abstractmethod
    async def scrape_one(self, target: str) -> Optional[dict]:
        """Scrape a single target and return a record dict or None."""
        ...
