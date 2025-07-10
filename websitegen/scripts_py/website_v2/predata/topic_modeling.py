# topic_modeling.py
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import LatentDirichletAllocation
import pandas as pd

def train_lda_model(headlines, n_topics=5, max_features=5000):
    """
    Train an LDA model on headlines and return the model and TF-IDF vectorizer.
    """
    # Extract titles from headlines
    texts = [article["title"] for article in headlines]

    # Convert text to TF-IDF features
    tfidf_vectorizer = TfidfVectorizer(max_features=max_features)
    X = tfidf_vectorizer.fit_transform(texts)

    # Train LDA model
    lda = LatentDirichletAllocation(n_components=n_topics, random_state=42)
    lda.fit(X)

    return lda, tfidf_vectorizer, X

def print_top_words(model, feature_names, n_top_words=10):
    """
    Print top words for each topic.
    """
    for topic_idx, topic in enumerate(model.components_):
        print(f"Topic {topic_idx}:")
        print(" ".join([feature_names[i] for i in topic.argsort()[:-n_top_words - 1:-1]]))

def get_topic_assignments(lda_model, tfidf_vectorizer, headlines):
    """
    Assign topics to each headline based on the LDA model.
    """
    texts = [article["title"] for article in headlines]
    X = tfidf_vectorizer.transform(texts)
    topic_assignments = lda_model.transform(X)
    return topic_assignments.argmax(axis=1)
