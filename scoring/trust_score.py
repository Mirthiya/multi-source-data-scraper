def calculate_trust_score(author_score, citation_score,
                          domain_score, recency_score,
                          disclaimer_score):

    trust_score = (
        0.25 * author_score +
        0.20 * citation_score +
        0.20 * domain_score +
        0.20 * recency_score +
        0.15 * disclaimer_score
    )

    return round(trust_score, 2)