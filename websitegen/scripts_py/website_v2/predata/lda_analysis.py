# lda_analysis.py
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import LatentDirichletAllocation
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from sklearn.manifold import TSNE
import pandas as pd
from collections import defaultdict

def train_lda_model(headlines, n_topics=5, max_features=5000):
    """
    Train an LDA model on headlines and return the model and TF-IDF vectorizer.
    """
    texts = [article["title"] for article in headlines]
    tfidf_vectorizer = TfidfVectorizer(max_features=max_features)
    X = tfidf_vectorizer.fit_transform(texts)
    lda = LatentDirichletAllocation(n_components=n_topics, random_state=42)
    lda.fit(X)
    return lda, tfidf_vectorizer, X

def get_topic_assignments(lda_model, tfidf_vectorizer, headlines):
    """Assign topics to each headline."""
    texts = [article["title"] for article in headlines]
    X = tfidf_vectorizer.transform(texts)
    topic_assignments = lda_model.transform(X)
    return topic_assignments.argmax(axis=1)

def plot_top_words(lda_model, feature_names, n_top_words=10, title="Top Words per Topic"):
    """Plot top words for each topic."""
    plt.figure(figsize=(12, 8))
    for i, topic in enumerate(lda_model.components_):
        top_words = [feature_names[j] for j in topic.argsort()[:-n_top_words - 1:-1]]
        plt.subplot(3, 2, i + 1)
        plt.barh(top_words, topic.argsort()[:-n_top_words - 1:-1])
        plt.xlabel("Probability")
        plt.title(f"Topic {i}")
    plt.tight_layout()
    plt.show()

def plot_topic_distribution(headlines, topic_assignments):
    """Plot distribution of topics across headlines."""
    topic_counts = pd.Series(topic_assignments).value_counts()
    plt.figure(figsize=(8, 6))
    sns.barplot(x=topic_counts.index, y=topic_counts.values)
    plt.title("Topic Distribution Across Headlines")
    plt.xlabel("Topic")
    plt.ylabel("Number of Headlines")
    plt.show()

def visualize_topics_with_tsne(lda_model, tfidf_vectorizer, headlines, topic_assignments):
    """Visualize topics in 2D space using t-SNE."""
    texts = [article["title"] for article in headlines]
    X = tfidf_vectorizer.transform(texts)
    tsne = TSNE(n_components=2, random_state=42)
    X_tsne = tsne.fit_transform(X.toarray())
    plt.figure(figsize=(10, 8))
    sns.scatterplot(x=X_tsne[:, 0], y=X_tsne[:, 1], hue=topic_assignments, palette='viridis')
    plt.title("Headlines in 2D Space by Topic")
    plt.legend(title="Topic")
    plt.show()
