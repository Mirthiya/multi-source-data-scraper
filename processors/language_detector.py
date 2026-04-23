"""
Language Detector
=================
Detects content language and filters non-English records.
Uses langdetect (wraps Google's language-detection library).
Falls back to simple heuristics if unavailable.
"""

import logging
import re

logger = logging.getLogger(__name__)

ENGLISH_COMMON_WORDS = {"the", "and", "is", "in", "of", "to", "a", "that", "for", "it"}


class LanguageDetector:
    def __init__(self):
        self._has_langdetect = self._check_langdetect()

    def filter_english(self, records: list[dict]) -> list[dict]:
        results = []
        for r in records:
            text = r.get("content", "") or r.get("title", "")
            lang = self._detect(text[:500])
            r["language"] = lang
            if lang == "en":
                results.append(r)
            else:
                logger.debug(f"LanguageDetector: filtered {r.get('url', '')} (lang={lang})")
        return results

    def _detect(self, text: str) -> str:
        if not text.strip():
            return "unknown"

        if self._has_langdetect:
            try:
                from langdetect import detect
                return detect(text)
            except Exception:
                pass

        # Heuristic fallback: check proportion of common English words
        words = set(re.findall(r"\b[a-z]{2,}\b", text.lower()))
        overlap = len(words & ENGLISH_COMMON_WORDS)
        return "en" if overlap >= 3 else "unknown"

    def _check_langdetect(self) -> bool:
        try:
            import langdetect
            return True
        except ImportError:
            logger.warning("langdetect not installed — using heuristic language detection")
            return False
