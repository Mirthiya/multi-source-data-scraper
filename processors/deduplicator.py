"""
Deduplicator
============
Removes near-duplicate content using TF-IDF cosine similarity.

Problem: Same article might be scraped from blog + Reddit discussion.
Solution: Pairwise cosine similarity matrix → flag pairs above threshold.

Threshold=0.85 means "85% similar content" → treat as duplicate.
Keeps the record with the higher trust-relevant metadata
(more authors, has citations, more recent date).

Also flags exact URL duplicates regardless of similarity.
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)


class Deduplicator:
    """
    Content-based deduplication using TF-IDF cosine similarity.
    O(n²) pairwise comparison — suitable for corpora up to ~10k documents.
    """

    def __init__(self, threshold: float = 0.85):
        self.threshold = threshold

    def deduplicate(self, records: list[dict]) -> tuple[list[dict], dict]:
        """
        Returns (deduplicated_records, report_dict).
        Report includes: total, kept, removed, duplicate_pairs.
        """
        if not records:
            return records, {"total": 0, "kept": 0, "removed": 0, "pairs": []}

        n_before = len(records)

        # Step 1: Remove exact URL duplicates
        records = self._dedup_by_url(records)

        # Step 2: Content similarity dedup
        records, pairs = self._dedup_by_similarity(records)

        n_after = len(records)
        report = {
            "total": n_before,
            "kept": n_after,
            "removed": n_before - n_after,
            "threshold": self.threshold,
            "duplicate_pairs": pairs[:10],  # keep top 10 for report
        }

        logger.info(
            f"Deduplicator: {n_before} → {n_after} records "
            f"({n_before - n_after} duplicates removed, threshold={self.threshold})"
        )
        return records, report

    # ── Dedup Methods ──────────────────────────────────────────────────────────

    def _dedup_by_url(self, records: list[dict]) -> list[dict]:
        seen_urls = set()
        unique = []
        for r in records:
            url = r.get("url", "")
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique.append(r)
        removed = len(records) - len(unique)
        if removed:
            logger.debug(f"Deduplicator: removed {removed} exact URL duplicates")
        return unique

    def _dedup_by_similarity(self, records: list[dict]) -> tuple[list[dict], list[dict]]:
        """
        Build TF-IDF matrix, compute pairwise cosine similarity,
        flag near-duplicates, keep the better record from each pair.
        """
        try:
            from sklearn.feature_extraction.text import TfidfVectorizer
            from sklearn.metrics.pairwise import cosine_similarity
            import numpy as np
        except ImportError:
            logger.warning("sklearn not available — skipping similarity dedup")
            return records, []

        texts = [
            (r.get("content") or r.get("title") or "")[:2000]
            for r in records
        ]

        # Need at least 2 documents
        if len(texts) < 2:
            return records, []

        vectorizer = TfidfVectorizer(max_features=3000, stop_words="english")
        try:
            matrix = vectorizer.fit_transform(texts)
        except ValueError:
            return records, []

        sim_matrix = cosine_similarity(matrix)

        # Find pairs above threshold
        to_remove = set()
        pairs_found = []

        for i in range(len(records)):
            if i in to_remove:
                continue
            for j in range(i + 1, len(records)):
                if j in to_remove:
                    continue
                sim = float(sim_matrix[i, j])
                if sim >= self.threshold:
                    # Keep the "better" record
                    loser = self._pick_loser(records[i], records[j], i, j)
                    to_remove.add(loser)
                    pairs_found.append({
                        "record_a": records[i].get("url", f"idx:{i}"),
                        "record_b": records[j].get("url", f"idx:{j}"),
                        "similarity": round(sim, 3),
                        "removed": records[loser].get("url", f"idx:{loser}"),
                    })

        unique = [r for idx, r in enumerate(records) if idx not in to_remove]
        return unique, pairs_found

    def _pick_loser(self, a: dict, b: dict, idx_a: int, idx_b: int) -> int:
        """
        Given two near-duplicate records, decide which to remove.
        Scoring: citations > authors > recency > word count.
        Higher score = keep.
        """
        def quality_score(r: dict) -> float:
            score = 0
            if r.get("has_citations"):
                score += 3
            if r.get("authors"):
                score += len(r["authors"]) * 0.5
            if r.get("date"):
                try:
                    score += float(r["date"][:4]) / 100  # recency proxy
                except Exception:
                    pass
            score += min(r.get("word_count", 0), 1000) / 1000
            if r.get("is_trusted_domain"):
                score += 2
            return score

        score_a = quality_score(a)
        score_b = quality_score(b)
        return idx_b if score_a >= score_b else idx_a
