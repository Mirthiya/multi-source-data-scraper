"""
Exporter
========
Exports pipeline results to:
  1. scraped_data.json        — full structured records (with trust breakdown)
  2. scraped_data.csv         — flat summary table (for Excel/Tableau)
  3. evaluation_report.json   — full evaluation metrics
  4. trust_explainability.csv — per-record feature contribution table
"""

import csv
import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def export_results(records: list[dict], eval_report: dict, output_dir: Path):
    output_dir.mkdir(exist_ok=True)

    _export_json(records, output_dir / "scraped_data.json")
    _export_csv(records, output_dir / "scraped_data.csv")
    _export_eval_report(eval_report, output_dir / "evaluation_report.json")
    _export_trust_explainability(records, output_dir / "trust_explainability.csv")

    logger.info(f"Exporter: all outputs saved to {output_dir}/")


def _export_json(records: list[dict], path: Path):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2, ensure_ascii=False)
    logger.debug(f"Exported {len(records)} records → {path}")


def _export_csv(records: list[dict], path: Path):
    if not records:
        return
    fields = [
        "source_id", "source_type", "url", "domain", "title",
        "authors", "date", "word_count", "topics", "trust_score",
        "trust_confidence", "language", "has_citations", "is_trusted_domain",
    ]
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for r in records:
            row = {k: r.get(k, "") for k in fields}
            row["authors"] = "; ".join(r.get("authors", []))
            row["topics"] = "; ".join(r.get("topics", []))
            writer.writerow(row)
    logger.debug(f"Exported CSV summary → {path}")


def _export_eval_report(report: dict, path: Path):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    logger.debug(f"Exported evaluation report → {path}")


def _export_trust_explainability(records: list[dict], path: Path):
    """
    Flat CSV where each row = one record, columns = each trust feature's contribution.
    Enables stakeholders to audit exactly why a source got its trust score.
    """
    if not records or not records[0].get("trust_breakdown"):
        return

    feature_names = list(records[0]["trust_breakdown"].keys())
    fields = ["source_id", "source_type", "url", "trust_score", "trust_confidence"] + \
             [f"{f}_contribution" for f in feature_names] + \
             [f"{f}_value" for f in feature_names]

    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for r in records:
            row = {
                "source_id": r.get("source_id", ""),
                "source_type": r.get("source_type", ""),
                "url": r.get("url", ""),
                "trust_score": r.get("trust_score", ""),
                "trust_confidence": r.get("trust_confidence", ""),
            }
            for feat in feature_names:
                data = r.get("trust_breakdown", {}).get(feat, {})
                row[f"{feat}_contribution"] = data.get("contribution", 0)
                row[f"{feat}_value"] = data.get("raw_value", 0)
            writer.writerow(row)

    logger.debug(f"Exported trust explainability table → {path}")
