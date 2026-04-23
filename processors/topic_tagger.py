"""
Topic Tagger
============
Upgrades from TF-IDF to KeyBERT (BERT-based semantic keyword extraction).

Why KeyBERT over TF-IDF:
  - TF-IDF treats each word independently; misses phrases ("machine learning")
  - KeyBERT uses BERT embeddings → captures semantic meaning
  - KeyBERT handles short texts (YouTube descriptions) far better
  - Supports n-gram extraction (1-2 word keyphrases)

Also implements MMR (Maximal Marginal Relevance) to reduce redundancy
in extracted topics (e.g., won't return both "neural net" and "neural network").

Falls back to TF-IDF if KeyBERT is unavailable (graceful degradation).
"""

import logging
import re
from typing import Literal

logger = logging.getLogger(__name__)

# ── Topic Tagger ───────────────────────────────────────────────────────────────

class TopicTagger:
    """
    Semantic topic extractor.
    method="keybert"  → BERT-based (preferred)
    method="tfidf"    → classical baseline (fallback / comparison)
    method="hybrid"   → both, merged and deduplicated
    """

    def __init__(
        self,
        method: Literal["keybert", "tfidf", "hybrid"] = "keybert",
        top_n: int = 5,
    ):
        self.method = method
        self.top_n = top_n
        self._keybert_model = None
        self._tfidf_fitted = False
        self._vectorizer = None
        self._tfidf_matrix = None
        self._corpus = []

    # ── Public API ─────────────────────────────────────────────────────────────

    def tag_all(self, records: list[dict]) -> list[dict]:
        """Tag topics for all records. Fits TF-IDF on corpus if needed."""
        texts = [r.get("content", "") or r.get("title", "") for r in records]

        if self.method in ("tfidf", "hybrid"):
            self._fit_tfidf(texts)

        for i, record in enumerate(records):
            text = texts[i]
            if not text.strip():
                record["topics"] = []
                continue

            topics = self._extract_topics(text, i)
            record["topics"] = topics
            record["topic_method"] = self.method

        logger.info(
            f"TopicTagger: tagged {len(records)} records using {self.method}. "
            f"Sample: {records[0]['topics'] if records else []}"
        )
        return records

    # ── Extraction ─────────────────────────────────────────────────────────────

    def _extract_topics(self, text: str, doc_idx: int) -> list[str]:
        text = self._preprocess(text)

        if self.method == "keybert":
            return self._keybert_extract(text)
        elif self.method == "tfidf":
            return self._tfidf_extract(doc_idx)
        else:  # hybrid
            kb = set(self._keybert_extract(text))
            tf = set(self._tfidf_extract(doc_idx))
            merged = list(kb | tf)
            return merged[: self.top_n]

    def _keybert_extract(self, text: str) -> list[str]:
        """
        KeyBERT extraction with MMR diversity.
        Falls back to TF-IDF if KeyBERT unavailable.
        """
        try:
            model = self._get_keybert_model()
            # MMR (use_mmr=True) ensures diverse, non-redundant keyphrases
            keywords = model.extract_keywords(
                text,
                keyphrase_ngram_range=(1, 2),
                stop_words="english",
                use_mmr=True,
                diversity=0.5,
                top_n=self.top_n,
            )
            return [kw for kw, score in keywords if score > 0.1]
        except ImportError:
            logger.warning("KeyBERT not installed — falling back to TF-IDF")
            self._fit_tfidf([text])
            return self._tfidf_extract(0)
        except Exception as e:
            logger.warning(f"KeyBERT failed: {e} — using TF-IDF fallback")
            self._fit_tfidf([text])
            return self._tfidf_extract(0)

    def _tfidf_extract(self, doc_idx: int) -> list[str]:
        """Extract top TF-IDF keywords for document at doc_idx."""
        if self._tfidf_matrix is None or self._vectorizer is None:
            return []
        try:
            import numpy as np
            row = self._tfidf_matrix[doc_idx]
            feature_names = self._vectorizer.get_feature_names_out()
            scores = zip(feature_names, row.toarray()[0])
            sorted_scores = sorted(scores, key=lambda x: x[1], reverse=True)
            return [term for term, score in sorted_scores[: self.top_n] if score > 0]
        except Exception as e:
            logger.debug(f"TF-IDF extract error: {e}")
            return []

    # ── Helpers ────────────────────────────────────────────────────────────────

    def _fit_tfidf(self, texts: list[str]):
        try:
            from sklearn.feature_extraction.text import TfidfVectorizer
            self._vectorizer = TfidfVectorizer(
                max_features=5000,
                ngram_range=(1, 2),
                stop_words="english",
                min_df=1,
            )
            cleaned = [self._preprocess(t) for t in texts]
            self._tfidf_matrix = self._vectorizer.fit_transform(cleaned)
            self._tfidf_fitted = True
        except Exception as e:
            logger.error(f"TF-IDF fitting failed: {e}")

    def _get_keybert_model(self):
        """Lazy-load KeyBERT (downloads model on first use ~400MB)."""
        if self._keybert_model is None:
            from keybert import KeyBERT
            # Use lightweight sentence-transformers model
            self._keybert_model = KeyBERT(model="all-MiniLM-L6-v2")
            logger.info("TopicTagger: KeyBERT model loaded (all-MiniLM-L6-v2)")
        return self._keybert_model

    def _preprocess(self, text: str) -> str:
        text = text.lower()
        text = re.sub(r"http\S+", "", text)       # remove URLs
        text = re.sub(r"[^a-z0-9\s]", " ", text)  # keep alphanumeric
        text = re.sub(r"\s+", " ", text)
        return text.strip()


# ── Benchmark: KeyBERT vs TF-IDF ──────────────────────────────────────────────

def compare_methods(sample_texts: list[str], top_n: int = 5) -> dict:
    """
    Run both methods on sample texts and return comparison results.
    Useful for evaluation report.
    """
    results = {}

    for method in ("keybert", "tfidf"):
        tagger = TopicTagger(method=method, top_n=top_n)
        fake_records = [{"content": t, "title": ""} for t in sample_texts]
        tagged = tagger.tag_all(fake_records)
        results[method] = [r["topics"] for r in tagged]

    return results
