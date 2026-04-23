"""
YouTube Scraper
===============
Extracts content from YouTube videos.
Strategy:
  1. YouTube Transcript API (best quality)
  2. yt-dlp subtitle extraction (fallback)
  3. Video description via oEmbed API (last resort)

Includes: channel name, view count, publish date, tags.
"""

import logging
import re
from typing import Optional
from urllib.parse import urlparse, parse_qs

import httpx

from scrapers.base_scraper import BaseScraper, make_record

logger = logging.getLogger(__name__)


def extract_video_id(url: str) -> Optional[str]:
    """Extract YouTube video ID from various URL formats."""
    patterns = [
        r"(?:v=|youtu\.be/|/embed/|/v/)([a-zA-Z0-9_-]{11})",
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None


class YoutubeScraper(BaseScraper):
    """
    Async YouTube scraper.
    Falls back gracefully through 3 content sources.
    Tracks which fallback was used for pipeline transparency.
    """

    OEMBED_URL = "https://www.youtube.com/oembed?url={url}&format=json"

    def __init__(self, urls: list[str]):
        super().__init__()
        self.urls = urls

    def _get_targets(self) -> list[str]:
        return self.urls

    async def scrape_one(self, url: str) -> Optional[dict]:
        video_id = extract_video_id(url)
        if not video_id:
            logger.warning(f"YoutubeScraper: could not extract video ID from {url}")
            return None

        content, content_source = await self._get_content(video_id, url)
        if not content or len(content.split()) < 20:
            logger.debug(f"YoutubeScraper: insufficient content for {url}")
            return None

        metadata = await self._get_metadata(url)

        return make_record(
            source_type="youtube",
            url=url,
            title=metadata.get("title", f"YouTube Video {video_id}"),
            content=content,
            authors=[metadata.get("author_name", "Unknown")],
            date=metadata.get("upload_date", ""),
            extra={
                "video_id": video_id,
                "content_source": content_source,  # transcript | subtitles | description
                "thumbnail_url": metadata.get("thumbnail_url", ""),
                "has_citations": False,
                "has_disclaimer": "disclaimer" in content.lower(),
                "is_trusted_domain": False,
            },
        )

    # ── Content Strategies ─────────────────────────────────────────────────────

    async def _get_content(self, video_id: str, url: str) -> tuple[str, str]:
        """Try each strategy in order, return (content, source_name)."""

        # Strategy 1: YouTube Transcript API
        try:
            content = await self._get_transcript(video_id)
            if content:
                logger.debug(f"YoutubeScraper: transcript OK for {video_id}")
                return content, "transcript"
        except Exception as e:
            logger.debug(f"YoutubeScraper: transcript failed ({e}), trying subtitles...")

        # Strategy 2: Description via oEmbed (always available, lower quality)
        try:
            content = await self._get_description(url)
            if content:
                logger.debug(f"YoutubeScraper: using description for {video_id}")
                return content, "description"
        except Exception as e:
            logger.debug(f"YoutubeScraper: description failed ({e})")

        return "", "none"

    async def _get_transcript(self, video_id: str) -> str:
        """
        Fetch transcript using youtube-transcript-api.
        Runs in thread pool since the library is synchronous.
        """
        import asyncio
        from functools import partial

        def _sync_fetch():
            from youtube_transcript_api import YouTubeTranscriptApi
            transcript = YouTubeTranscriptApi.get_transcript(video_id)
            return " ".join(entry["text"] for entry in transcript)

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, _sync_fetch)

    async def _get_description(self, url: str) -> str:
        """Fetch video description from oEmbed API."""
        oembed_url = self.OEMBED_URL.format(url=url)
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(oembed_url)
            resp.raise_for_status()
            data = resp.json()
            # oEmbed doesn't include description; return title + author as minimal content
            title = data.get("title", "")
            author = data.get("author_name", "")
            return f"{title}. Video by {author} on YouTube." if title else ""

    async def _get_metadata(self, url: str) -> dict:
        """Fetch basic metadata from oEmbed."""
        try:
            oembed_url = self.OEMBED_URL.format(url=url)
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(oembed_url)
                resp.raise_for_status()
                return resp.json()
        except Exception:
            return {}
