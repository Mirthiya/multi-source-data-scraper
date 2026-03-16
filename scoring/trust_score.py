from datetime import datetime

def calculate_trust_score(author, citations, domain, year, disclaimer):

    # Author credibility
    if author:
        author_score = 0.8
    else:
        author_score = 0.3

    # Citation score
    if citations > 50:
        citation_score = 1
    elif citations > 10:
        citation_score = 0.7
    else:
        citation_score = 0.3

    # Domain authority
    trusted_domains = ["nature.com", "who.int", "nih.gov", "pubmed"]
    if any(d in domain for d in trusted_domains):
        domain_score = 1
    else:
        domain_score = 0.5

    # Recency score
    current_year = datetime.now().year
    age = current_year - year

    if age <= 2:
        recency_score = 1
    elif age <= 5:
        recency_score = 0.7
    else:
        recency_score = 0.4

    # Medical disclaimer
    disclaimer_score = 1 if disclaimer else 0.5

    trust_score = (
        0.25 * author_score +
        0.20 * citation_score +
        0.20 * domain_score +
        0.20 * recency_score +
        0.15 * disclaimer_score
    )

    return round(trust_score, 2)
