from sklearn.feature_extraction.text import TfidfVectorizer

def extract_topics(text_list, top_n=5):

    # Safety check: if input is None
    if not text_list:
        return []

    # Remove empty or very short text
    cleaned = []
    for t in text_list:
        if isinstance(t, str) and len(t.strip()) > 20:
            cleaned.append(t.strip())

    # If nothing usable remains
    if len(cleaned) == 0:
        return []

    text = " ".join(cleaned)

    try:
        vectorizer = TfidfVectorizer(stop_words="english", max_features=50)
        X = vectorizer.fit_transform([text])

        words = vectorizer.get_feature_names_out()

        if len(words) == 0:
            return []

        return list(words[:top_n])

    except Exception:
        return []
