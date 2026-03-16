from sklearn.feature_extraction.text import TfidfVectorizer

def extract_topics(text_list, top_n=5):
    text = " ".join(text_list)

    vectorizer = TfidfVectorizer(stop_words="english")
    X = vectorizer.fit_transform([text])

    feature_array = vectorizer.get_feature_names_out()
    tfidf_scores = X.toarray()[0]

    word_scores = list(zip(feature_array, tfidf_scores))
    sorted_words = sorted(word_scores, key=lambda x: x[1], reverse=True)

    topics = [word for word, score in sorted_words[:top_n]]

    return topics
