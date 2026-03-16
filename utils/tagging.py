from sklearn.feature_extraction.text import TfidfVectorizer

def extract_topics(text_list, top_n=5):

    # remove empty strings
    text_list = [t for t in text_list if t.strip() != ""]

    if len(text_list) == 0:
        return []

    text = " ".join(text_list)

    try:
        vectorizer = TfidfVectorizer(stop_words="english")
        X = vectorizer.fit_transform([text])

        feature_array = vectorizer.get_feature_names_out()
        scores = X.toarray()[0]

        word_scores = list(zip(feature_array, scores))
        sorted_words = sorted(word_scores, key=lambda x: x[1], reverse=True)

        topics = [word for word, score in sorted_words[:top_n]]

        return topics

    except:
        return []
