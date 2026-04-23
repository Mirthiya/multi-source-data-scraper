# Multi-Source Data Scraping Pipeline v2

Production-style pipeline for collecting, enriching, scoring, and ranking content across multiple sources with explainable trust intelligence.

---

## What This Project Solves

In real-world systems, not all information is reliable.

This project addresses a key question:

**Which sources are actually trustworthy, and why?**

It builds an end-to-end pipeline that not only collects data, but evaluates credibility, ranks sources, and explains decisions in a transparent way.

---

## What This Pipeline Does

1. Scrapes content from multiple sources (Blogs, YouTube, PubMed, Reddit)
2. Cleans and processes text using NLP
3. Removes duplicate or low-quality data
4. Assigns a trust score (0–1) using multi-feature logic
5. Ranks sources based on credibility
6. Provides explainability for every score
7. Outputs structured datasets for downstream use

---

## Evolution: v1 → v2 Improvements

| Area           | v1 (Initial Version) | v2 (Current Version)                          |
| -------------- | -------------------- | --------------------------------------------- |
| Scraping       | Synchronous, fragile | Async (`httpx`), retry + fault-tolerant       |
| Sources        | Limited              | Multi-source (Blogs, YouTube, PubMed, Reddit) |
| Error Handling | Minimal              | Handles 403s, missing data, fallback strategy |
| NLP            | Basic (TF-IDF)       | KeyBERT (semantic embeddings)                 |
| Deduplication  | Not implemented      | Cosine similarity-based                       |
| Trust Scoring  | Fixed weights        | Multi-feature + explainable + domain-aware    |
| Ranking        | Not available        | Top trusted source ranking                    |
| Explainability | None                 | Feature-level trust breakdown                 |
| Evaluation     | None                 | Full pipeline metrics                         |
| System Design  | Script-level         | Modular, production-style pipeline            |

---

## What Makes This Project Different

* Handles real-world scraping failures such as 403 errors and missing data
* Uses fallback strategies to guarantee minimum dataset availability
* Implements explainable trust scoring instead of black-box models
* Supports ranking of top trusted sources
* Designed as a modular, production-style pipeline

---

## Architecture

```
Data Sources
   ↓
Async Scrapers (Fault-Tolerant)
   ↓
Language Filtering + Cleaning
   ↓
Semantic Topic Extraction (KeyBERT)
   ↓
Deduplication (Cosine Similarity)
   ↓
Trust Scoring (Explainable + Feature-Based)
   ↓
Ranking Engine (Top Trusted Sources)
   ↓
Evaluation Metrics
   ↓
Structured Output (JSON + CSV)
```

---

## Data Sources

* Blogs (articles)
* YouTube (transcripts or descriptions)
* PubMed (research papers)
* Reddit (community discussions)

---

## Core Features

### Async Multi-Source Scraping

* Built using asyncio and httpx
* Retry with exponential backoff
* Failure isolation to prevent pipeline crashes

---

### NLP Processing

* Language detection (English filtering)
* Text cleaning and normalization
* Content chunking for analysis

---

### Semantic Topic Extraction (KeyBERT)

* Uses transformer embeddings (`all-MiniLM-L6-v2`)
* Captures semantic meaning rather than keyword frequency
* MMR ensures diverse topic coverage

---

### Deduplication Engine

* Removes redundant content across sources
* Cosine similarity threshold = 0.85
* Retains highest-quality version

---

### Explainable Trust Scoring

Each record is scored using multiple signals:

* Domain authority
* Author credibility
* Citation presence
* Recency
* Content quality

Additional scoring adjustments:

* PubMed sources receive higher trust weighting
* Wikipedia receives moderate trust adjustment
* Longer content receives higher reliability weighting

Each score includes a feature-level breakdown for transparency.

---

### Ranking Engine

```python
top_k = sorted(data, key=lambda x: x["trust_score"], reverse=True)[:5]
```

* Identifies top trusted sources
* Enables filtering of high-quality data
* Useful for retrieval-augmented systems and downstream ML pipelines

---

## Example Pipeline Output

```
Top Trusted Sources:
1. pubmed | Score: 0.89
2. reddit | Score: 0.79
3. reddit | Score: 0.75
4. reddit | Score: 0.65
5. reddit | Score: 0.63

Source Distribution:
{'blog': 4, 'pubmed': 1, 'reddit': 10, 'youtube': 2}

Evaluation Summary:
- Total records: 17
- Source coverage: 100%
- Average trust score: ~0.5
```

---

## Evaluation Metrics

The pipeline evaluates:

* Data completeness
* Source coverage
* Topic richness
* Deduplication effectiveness
* Trust score distribution

---

## Project Structure

```
multi-source-data-scraper/
│
├── main.py
├── requirements.txt
│
├── scrapers/       # Source-specific scrapers
├── processors/     # NLP and cleaning
├── trust/          # Trust scoring logic
├── evaluation/     # Metrics and analysis
├── utils/          # Helper utilities
```

---

## How to Run

```bash
git clone https://github.com/Mirthiya/multi-source-data-scraper
cd multi-source-data-scraper

pip install -r requirements.txt
python main.py
```

---

## Expected Output

Running the pipeline generates:

* Ranked list of trusted sources
* Explainable trust scores for each record
* Evaluation metrics (coverage, quality, diversity)
* Structured datasets in JSON and CSV formats

---

## Output Files

| File                     | Description                   |
| ------------------------ | ----------------------------- |
| scraped_data.json        | Full structured dataset       |
| scraped_data.csv         | Tabular format                |
| evaluation_report.json   | Pipeline metrics              |
| trust_explainability.csv | Feature-level trust breakdown |

---

## Sample Output

```json
{
  "source_type": "pubmed",
  "author": "Research Team",
  "topic_tags": ["cancer therapy", "nanotechnology"],
  "trust_score": 0.89,
  "trust_breakdown": {
    "domain_authority": 1.0,
    "citation_presence": 1.0,
    "pubmed_boost": 0.1
  }
}
```

---

## Key Insights

* Academic sources such as PubMed consistently achieve higher trust scores
* Community platforms such as Reddit provide volume but lower reliability
* Trust scoring requires combining multiple signals rather than relying on a single factor
* Explainability is essential for understanding and validating model decisions

---

## Tech Stack

* Python
* httpx (asynchronous scraping)
* KeyBERT (semantic NLP)
* scikit-learn (similarity and deduplication)
* JSON and CSV

---

## Future Improvements

* LLM-based summarization (GPT or Mistral)
* Vector database integration (FAISS or Pinecone)
* FastAPI deployment
* Scheduled pipelines using Airflow

---

## Final Note

This project demonstrates a complete data pipeline that goes beyond simple scraping:

* Robust data engineering
* Semantic understanding of content
* Explainable trust scoring
* Practical system design

Built with a focus on scalability, reliability, and trust-aware data processing.
