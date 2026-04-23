"""
PubMed Scraper
==============
Scrapes academic articles from PubMed.
Uses both:
  1. PubMed HTML page parsing (abstract, authors, date, MeSH terms)
  2. NCBI E-utilities API (structured metadata, citation count proxy)

PubMed is well-structured; this scraper extracts rich metadata
that significantly boosts trust scores (citations, authors, DOI).
"""

import logging
import re
from typing import Optional

from bs4 import BeautifulSoup

from scrapers.base_scraper import BaseScraper, make_record

logger = logging.getLogger(__name__)

NCBI_EUTILS = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"


class PubMedScraper(BaseScraper):
    """
    Async PubMed scraper with NCBI API fallback.
    Extracts: title, abstract, authors, DOI, journal, MeSH terms, citation signals.
    """

    def __init__(self, urls: list[str]):
        super().__init__()
        self.urls = urls

    def _get_targets(self) -> list[str]:
        return self.urls

    async def scrape_one(self, url: str) -> Optional[dict]:
        pmid = self._extract_pmid(url)
        if not pmid:
            logger.warning(f"PubMedScraper: cannot extract PMID from {url}")
            return None

        # Try API first (more structured), fallback to HTML
        record_data = await self._fetch_via_api(pmid) or await self._fetch_via_html(url)
        if not record_data:
            return None

        return make_record(
            source_type="pubmed",
            url=url,
            title=record_data.get("title", ""),
            content=record_data.get("abstract", ""),
            authors=record_data.get("authors", []),
            date=record_data.get("date", ""),
            extra={
                "pmid": pmid,
                "doi": record_data.get("doi", ""),
                "journal": record_data.get("journal", ""),
                "mesh_terms": record_data.get("mesh_terms", []),
                "has_citations": True,      # PubMed articles always cite sources
                "is_trusted_domain": True,  # PubMed = NIH = authoritative
                "has_disclaimer": False,
                "citation_count_proxy": record_data.get("citation_count_proxy", 0),
            },
        )

    # ── NCBI E-utilities API ───────────────────────────────────────────────────

    async def _fetch_via_api(self, pmid: str) -> Optional[dict]:
        """
        Fetch structured metadata from NCBI E-utilities.
        Returns a dict with article metadata or None on failure.
        """
        try:
            url = f"{NCBI_EUTILS}/esummary.fcgi?db=pubmed&id={pmid}&retmode=json"
            response = await self._fetch(url)
            response.raise_for_status()
            data = response.json()

            result = data.get("result", {}).get(pmid, {})
            if not result:
                return None

            authors = [
                a.get("name", "") for a in result.get("authors", [])
            ]
            date = result.get("pubdate", "")[:10] if result.get("pubdate") else ""

            # Fetch abstract via efetch
            abstract = await self._fetch_abstract(pmid)

            return {
                "title": result.get("title", "").rstrip("."),
                "abstract": abstract,
                "authors": authors,
                "date": date,
                "doi": next(
                    (
                        id_obj.get("value", "")
                        for id_obj in result.get("articleids", [])
                        if id_obj.get("idtype") == "doi"
                    ),
                    "",
                ),
                "journal": result.get("source", ""),
                "citation_count_proxy": len(result.get("references", [])),
            }
        except Exception as e:
            logger.debug(f"PubMedScraper API failed for {pmid}: {e}")
            return None

    async def _fetch_abstract(self, pmid: str) -> str:
        try:
            url = f"{NCBI_EUTILS}/efetch.fcgi?db=pubmed&id={pmid}&rettype=abstract&retmode=text"
            response = await self._fetch(url)
            text = response.text.strip()
            # Extract just the abstract section
            lines = text.split("\n")
            abstract_lines = []
            in_abstract = False
            for line in lines:
                if "Abstract" in line or "ABSTRACT" in line:
                    in_abstract = True
                    continue
                if in_abstract:
                    if line.strip() and line[0].isupper() and len(line) < 30:
                        break  # New section started
                    abstract_lines.append(line)
            abstract = " ".join(abstract_lines).strip()
            return abstract if len(abstract) > 50 else text[:1000]
        except Exception:
            return ""

    # ── HTML Fallback ──────────────────────────────────────────────────────────

    async def _fetch_via_html(self, url: str) -> Optional[dict]:
        response = await self._fetch(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        title_el = soup.select_one("h1.heading-title, .article-title")
        title = title_el.get_text().strip() if title_el else "Untitled"

        abstract_el = soup.select_one("#abstract, .abstract-content, [data-testid='abstract']")
        abstract = abstract_el.get_text(separator=" ").strip() if abstract_el else ""

        authors = [
            a.get_text().strip()
            for a in soup.select(".authors-list .author-name, .contrib-author")
        ][:10]

        date_el = soup.select_one(".article-date, time")
        date = date_el.get_text().strip()[:10] if date_el else ""

        doi_el = soup.find("a", href=re.compile(r"doi\.org"))
        doi = doi_el["href"].split("doi.org/")[-1] if doi_el else ""

        mesh_terms = [
            el.get_text().strip()
            for el in soup.select(".mesh-list a, [data-testid='mesh-term']")
        ]

        return {
            "title": title,
            "abstract": abstract,
            "authors": authors,
            "date": date,
            "doi": doi,
            "journal": "",
            "mesh_terms": mesh_terms,
            "citation_count_proxy": 1 if doi else 0,
        }

    def _extract_pmid(self, url: str) -> Optional[str]:
        match = re.search(r"/(\d{6,9})/?", url)
        return match.group(1) if match else None
