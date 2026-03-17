# Multi-Source Data Scraping and Processing Pipeline

## Overview

This project is about building a simple **data scraping pipeline** that collects information from different types of sources like blogs, YouTube videos, and PubMed articles.

The main idea is to take raw data from these sources, process it, and store everything in a structured format (JSON). Along the way, the project also extracts useful information like topics and assigns a trust score to each source.

Through this project, I worked on:

* Web scraping
* Basic NLP (topic extraction)
* Data cleaning and structuring
* Building a small end-to-end pipeline

---

## Data Collection

The pipeline collects data from:

* **3 blog articles**
* **2 YouTube videos**
* **1 PubMed research article**

This was done to make sure the project handles multiple types of sources.

---

## What Data is Extracted

Each source is converted into a structured format with the following fields:

* `source_url` – link to the original content
* `source_type` – blog / youtube / pubmed
* `author` – author name or channel name
* `published_date` – when it was published
* `language` – detected language
* `region` – region (if available)
* `topic_tags` – important keywords extracted from content
* `trust_score` – score between 0 and 1
* `content_chunks` – text split into smaller parts

---

## What is Extracted from Each Source

### Blogs

* Title
* Author
* Published date
* Cleaned article text (removed unwanted parts)

### YouTube

* Channel name
* Publish date
* Video description
* Transcript (if available, otherwise description is used)

### PubMed

* Title
* Authors
* Journal name
* Abstract
* Year

---

## Features of the Project

The pipeline does the following:

* Scrapes data from multiple sources
* Extracts metadata
* Detects language
* Generates topic tags using TF-IDF
* Splits large text into chunks
* Calculates a trust score
* Saves everything into a JSON file

---

## Trust Score (How it Works)

Each source is given a score between **0 and 1** to estimate how reliable it is.

The score is based on:

* Author credibility
* Number of references (citations)
* Domain quality (trusted site or not)
* How recent the content is
* Whether any disclaimer is present

Formula used:

Trust Score =
0.25 × Author Credibility +
0.20 × Citation Count +
0.20 × Domain Authority +
0.20 × Recency +
0.15 × Disclaimer Presence

This is not perfect, but gives a reasonable estimate.

---

## Handling Edge Cases

Some common issues were handled:

* Missing author/date → default values used
* Multiple authors → combined into one field
* Empty content → skipped or handled safely
* Long articles → split into chunks
* Different languages → detected automatically

---

## Abuse / Data Quality Handling

To avoid low-quality or misleading data:

* Unknown authors → lower trust score
* Weak or spammy websites → lower domain score
* Outdated content → lower recency score
* Missing disclaimers → reduces trust

---

## Project Structure

```
multi-source-data-scraper
│
├── main.py
├── requirements.txt
├── README.md
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

## How to Run

Clone the repo:

```
git clone https://github.com/your-username/multi-source-data-scraper.git
```

Go to the folder:

```
cd multi-source-data-scraper
```

Install dependencies:

```
pip install -r requirements.txt
```

Run the project:

```
python main.py
```

---

## Viewing Output (Colab)

If you are using Google Colab:

```
!cat output/scraped_data.json
```

---

## Output

The output is stored in:

```
output/scraped_data.json
```

It contains processed data from all sources (blogs, YouTube, PubMed).

Note:
The output file in this repo is a **sample generated using Google Colab**, downloaded and uploaded here.

---

## Environment Used

* Python
* Google Colab
* GitHub

---

## Where This Can Be Used

This kind of pipeline can be extended for:

* Research data collection
* Building datasets for ML
* Content analysis
* Knowledge extraction systems

---

## Final Note

This project helped me understand how to combine **scraping + NLP + data processing** into a single pipeline.

It’s a basic version, but it can be improved further by adding better models, APIs, or scaling it.
