"""
Trust Scorer v2 — Adaptive with Explainability
"""

import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# ── Domain Trust Lists ───────────────────────────

HIGH_TRUST_DOMAINS = {
    "pubmed.ncbi.nlm.nih.gov", "arxiv.org", "nature.com", "science.org",
    "openai.com", "deepmind.com", "ieee.org", "acm.org", "nih.gov",
    "springer.com", "sciencedirect.com", "thelancet.com", "nejm.org",
}

MEDIUM_TRUST_DOMAINS = {
    "towardsdatascience.com", "medium.com", "machinelearningmastery.com",
    "blog.tensorflow.org", "pytorch.org", "huggingface.co", "github.io",
}

LOW_TRUST_DOMAINS = {
    "reddit.com", "quora.com", "stackexchange.com",
}

# ── Source baseline ─────────────────────────────

SOURCE_BASELINE = {
    "pubmed": 0.80,
    "blog":   0.50,
    "youtube": 0.40,
    "reddit": 0.30,
}

# ── Feature weights ─────────────────────────────

FEATURE_WEIGHTS = {
    "domain_authority":    0.22,
    "author_credibility":  0.18,
    "citation_presence":   0.18,
    "content_length":      0.10,
    "recency":             0.12,
    "source_baseline":     0.10,
    "disclaimer_penalty":  -0.05,
    "community_signal":    0.07,
    "has_doi":             0.08,
}


class TrustScorer:

    def score_all(self, records):
        for record in records:
            score, breakdown, confidence = self._score_record(record)
            record["trust_score"] = round(score, 4)
            record["trust_breakdown"] = breakdown
            record["trust_confidence"] = round(confidence, 3)
        return records

    # ── Scoring ──────────────────────────────────

    def _score_record(self, record):
        features = self._extract_features(record)
        breakdown = {}
        raw_score = 0.0

        # Base feature scoring
        for feature, weight in FEATURE_WEIGHTS.items():
            value = features.get(feature, 0.0)
            contribution = value * weight
            breakdown[feature] = {
                "raw_value": round(value, 4),
                "weight": weight,
                "contribution": round(contribution, 4),
            }
            raw_score += contribution

        # 🔥 Custom Boost Logic (EXPLAINABLE)

        if record.get("source_type") == "pubmed":
            raw_score += 0.1
            breakdown["pubmed_boost"] = {"contribution": 0.1}

        if "wikipedia" in record.get("domain", ""):
            raw_score += 0.05
            breakdown["wikipedia_boost"] = {"contribution": 0.05}

        if record.get("word_count", 0) > 200:
            raw_score += 0.05
            breakdown["length_boost"] = {"contribution": 0.05}

        # Clamp score
        final_score = max(0.0, min(1.0, raw_score))

        # Confidence score
        data_present = sum(
            1 for k, v in features.items()
            if v > 0 and k != "disclaimer_penalty"
        )
        confidence = data_present / len(features)

        return final_score, breakdown, confidence

    # ── Feature extraction ───────────────────────

    def _extract_features(self, record):
        domain = record.get("domain", "")
        source_type = record.get("source_type", "blog")
        authors = record.get("authors", [])
        date_str = record.get("date", "")

        return {
            "domain_authority": self._domain_authority(domain, record.get("is_trusted_domain", False)),
            "author_credibility": self._author_credibility(authors),
            "citation_presence": 1.0 if record.get("has_citations") else 0.0,
            "content_length": self._content_length_score(record.get("word_count", 0)),
            "recency": self._recency_score(date_str),
            "source_baseline": SOURCE_BASELINE.get(source_type, 0.4),
            "disclaimer_penalty": 1.0 if record.get("has_disclaimer") else 0.0,
            "community_signal": self._community_signal(record),
            "has_doi": 1.0 if record.get("doi") else 0.0,
        }

    # ── Feature helpers ──────────────────────────

    def _domain_authority(self, domain, is_trusted):
        if domain in HIGH_TRUST_DOMAINS or is_trusted:
            return 1.0
        if domain in MEDIUM_TRUST_DOMAINS:
            return 0.6
        if domain in LOW_TRUST_DOMAINS:
            return 0.2
        if domain.endswith((".edu", ".gov", ".org")):
            return 0.75
        return 0.35

    def _author_credibility(self, authors):
        n = len([a for a in authors if a and a != "Unknown"])
        if n == 0:
            return 0.0
        if n == 1:
            return 0.5
        return min(1.0, 0.5 + (n - 1) * 0.2)

    def _content_length_score(self, word_count):
        if word_count < 50:
            return 0.0
        if word_count < 200:
            return 0.3
        if word_count < 500:
            return 0.6
        if word_count <= 2000:
            return 1.0
        return max(0.5, 1.0 - (word_count - 2000) / 10000)

    def _recency_score(self, date_str):
        if not date_str:
            return 0.3
        try:
            year = int(date_str[:4])
            age = datetime.utcnow().year - year
            if age == 0:
                return 1.0
            if age == 1:
                return 0.85
            if age <= 3:
                return 0.65
            if age <= 5:
                return 0.45
            return max(0.1, 0.45 - (age - 5) * 0.05)
        except:
            return 0.3

    def _community_signal(self, record):
        if record.get("community_validated"):
            return 1.0
        ratio = record.get("upvote_ratio", 0)
        if ratio > 0.9:
            return 0.8
        if ratio > 0.75:
            return 0.5
        return 0.0

    # ── ✅ Report Helpers (FIX ADDED) ─────────────

    @staticmethod
    def summarize(records):
        """Generate trust score summary"""
        if not records:
            return {}

        scores = [r.get("trust_score", 0) for r in records]

        by_source = {}
        for r in records:
            st = r.get("source_type", "unknown")
            by_source.setdefault(st, []).append(r.get("trust_score", 0))

        return {
            "overall": {
                "mean": round(sum(scores) / len(scores), 3),
                "min": round(min(scores), 3),
                "max": round(max(scores), 3),
                "high_trust_pct": round(
                    sum(1 for s in scores if s >= 0.7) / len(scores) * 100, 1
                ),
            },
            "by_source_type": {
                st: {
                    "mean": round(sum(v) / len(v), 3),
                    "count": len(v),
                }
                for st, v in by_source.items()
            },
        }
