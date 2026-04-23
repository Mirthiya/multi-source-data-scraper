"""
Blog Scraper
============
Scrapes article content from blog URLs.
Handles paragraph extraction, title detection,
author extraction, and date parsing.
"""

import logging
import re
from typing import Optional

from bs4 import BeautifulSoup
from scrapers.base_scraper import BaseScraper, make_record

logger = logging.getLogger(__name__)

# Trusted academic / tech domains get a domain-authority boost in TrustScorer
TRUSTED_DOMAINS = {
    "arxiv.org", "nature.com", "sciencedirect.com", "springer.com",
    "towardsdatascience.com", "openai.com", "deepmind.com",
    "machinelearningmastery.com", "ieee.org", "acm.org",
}

SKIP_TAGS = {
    "nav", "footer", "header", "aside", "script",
    "style", "form", "noscript", "advertisement",
}


class BlogScraper(BaseScraper):
    """
    Async blog scraper with:
    - Smart paragraph extraction (skips nav/footer/ads)
    - Multiple title extraction strategies
    - Author and date heuristics
    - Minimum content length guard (30 words)
    """

    def __init__(self, urls: list[str]):
        super().__init__()
        self.urls = urls

    def _get_targets(self) -> list[str]:
        return self.urls

    async def scrape_one(self, url: str) -> Optional[dict]:
        response = await self._fetch(url)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        # Remove noise tags
        for tag in soup.find_all(SKIP_TAGS):
            tag.decompose()

        title = self._extract_title(soup)
        content = self._extract_content(soup)
        authors = self._extract_authors(soup)
        date = self._extract_date(soup)
        domain = self._extract_domain_flag(url)

        if len(content.split()) < 30:
            logger.debug(f"BlogScraper: skipping {url} (content too short)")
            return None

        return make_record(
            source_type="blog",
            url=url,
            title=title,
            content=content,
            authors=authors,
            date=date,
            extra={
                "is_trusted_domain": domain in TRUSTED_DOMAINS,
                "has_citations": self._has_citations(soup),
                "has_disclaimer": self._has_disclaimer(content),
            },
        )

    # ── Extraction Helpers ─────────────────────────────────────────────────────

    def _extract_title(self, soup: BeautifulSoup) -> str:
        for selector in ["h1", 'meta[property="og:title"]', "title"]:
            el = soup.select_one(selector)
            if el:
                return el.get("content", el.get_text()).strip()
        return "Untitled"

    def _extract_content(self, soup: BeautifulSoup) -> str:
        """
        Priority order:
        1. <article> tag (most blogs use semantic HTML)
        2. <main> tag
        3. Largest <div> by paragraph count
        4. All <p> tags as fallback
        """
        for container_tag in ["article", "main"]:
            container = soup.find(container_tag)
            if container:
                paragraphs = container.find_all("p")
                text = " ".join(p.get_text(separator=" ") for p in paragraphs)
                if len(text.split()) > 30:
                    return self._clean_text(text)

        # Fallback: find div with most paragraphs
        best_div, best_count = None, 0
        for div in soup.find_all("div"):
            count = len(div.find_all("p"))
            if count > best_count:
                best_div, best_count = div, count

        if best_div and best_count > 2:
            text = " ".join(p.get_text(separator=" ") for p in best_div.find_all("p"))
            return self._clean_text(text)

        # Last resort: all paragraphs
        return self._clean_text(
            " ".join(p.get_text(separator=" ") for p in soup.find_all("p"))
        )

    def _extract_authors(self, soup: BeautifulSoup) -> list[str]:
        authors = []

        # Try meta tags
        for meta_name in ["author", "article:author"]:
            el = soup.find("meta", attrs={"name": meta_name}) or \
                 soup.find("meta", attrs={"property": meta_name})
            if el:
                authors.append(el.get("content", "").strip())

        # Try common HTML patterns
        for selector in [".author", '[rel="author"]', ".byline", '[itemprop="author"]']:
            for el in soup.select(selector)[:3]:
                name = el.get_text().strip()
                if name and name not in authors:
                    authors.append(name)

        return [a for a in authors if a][:3]  # cap at 3 authors

    def _extract_date(self, soup: BeautifulSoup) -> str:
        for selector in [
            'meta[property="article:published_time"]',
            'meta[name="date"]',
            'time[datetime]',
        ]:
            el = soup.select_one(selector)
            if el:
                raw = el.get("content") or el.get("datetime") or el.get_text()
                try:
                    return raw.strip()[:10]  # YYYY-MM-DD
                except Exception:
                    pass
        return ""

    def _extract_domain_flag(self, url: str) -> str:
        from urllib.parse import urlparse
        return urlparse(url).netloc.replace("www.", "")

    def _has_citations(self, soup: BeautifulSoup) -> bool:
        text = soup.get_text().lower()
        return any(kw in text for kw in ["references", "bibliography", "doi:", "et al."])

    def _has_disclaimer(self, content: str) -> bool:
        return any(kw in content.lower() for kw in ["disclaimer", "opinion", "not medical advice"])

    def _clean_text(self, text: str) -> str:
        text = re.sub(r"\s+", " ", text)
        text = re.sub(r"[^\x20-\x7E\n]", " ", text)  # ASCII only
        return text.strip()
