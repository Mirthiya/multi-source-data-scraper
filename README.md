# multi-source-data-scraper
Multi-source web scraping and trust scoring system (blogs, YouTube, PubMed)
# Multi-Source Data Scraping and Processing Pipeline

## Overview

This project implements a **multi-source data scraping pipeline** that collects and processes information from different online sources including blogs, YouTube videos, and PubMed research articles.

The system extracts metadata, processes textual content, performs topic tagging, and computes a trust score for each source. The processed information is stored in a structured JSON format.

This project demonstrates skills in:

* Web scraping
* Data preprocessing
* Natural Language Processing (NLP)
* Data structuring
* Building automated data pipelines

---

## Data Sources

The pipeline collects information from the following sources:

* **Blogs**

  * Extracts article text, author, and publication date.

* **YouTube Videos**

  * Extracts video metadata and textual content (transcript or description).

* **PubMed Articles**

  * Extracts article metadata and abstract information.

---

## Extracted Fields

Each scraped source is structured into the following format:

* `source_url` – URL of the source
* `source_type` – Type of source (blog, youtube, pubmed)
* `author` – Author or channel name
* `published_date` – Publication date
* `language` – Detected language
* `region` – Region information (if available)
* `topic_tags` – Extracted keywords using NLP
* `trust_score` – Calculated credibility score
* `content_chunks` – Processed text split into smaller segments

---

## Features

The pipeline performs the following operations:

1. **Multi-source scraping**
2. **Metadata extraction**
3. **Language detection**
4. **Topic extraction using TF-IDF**
5. **Content chunking**
6. **Trust score calculation**
7. **Structured JSON output generation**

---

## Project Structure

```
multi-source-data-scraper
│
├── main.py
├── requirements.txt
│
├── scrapers
│   ├── blog_scraper.py
│   ├── youtube_scraper.py
│   └── pubmed_scraper.py
│
├── utils
│   ├── chunking.py
│   ├── tagging.py
│   └── trust_score.py
│
└── output
    └── scraped_data.json
```

---

## Installation

Clone the repository:

```
git clone https://github.com/Mirthiya/multi-source-data-scraper.git
```

Navigate to the project folder:

```
cd multi-source-data-scraper
```

Install dependencies:

```
pip install -r requirements.txt
```

---

## Running the Project

Run the main pipeline:

```
python main.py
```

This will scrape data from all configured sources and generate the output file.

---

## Viewing the Output (Google Colab)

To view the output file in Google Colab:

```
!cat output/scraped_data.json
```

## Output

The pipeline generates the following file:

```
output/scraped_data.json
```

This JSON file contains processed data from:

* Blog articles
* YouTube videos
* PubMed research articles

Each entry contains metadata, topic tags, trust score, and chunked content.

## Environment

This project was developed and executed using:

* Python
* Google Colab
* GitHub

---

## Applications

This pipeline can be extended for:

* Research data aggregation
* Knowledge extraction systems
* AI training datasets
* Content analysis platforms
