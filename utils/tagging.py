from sklearn.feature_extraction.text import TfidfVectorizer

def extract_topics(text_list, top_n=5):
    vectorizer = TfidfVectorizer(stop_words="english")
    X = vectorizer.fit_transform(text_list)

    features = vectorizer.get_feature_names_out()
    return features[:top_n]