# main.py
import sys
sys.path.append('.')  # Add current directory to Python path

from rss_fetcher import get_rss_headlines
from nlp_utils import *
from event_analyzer import EventAnalyzer
from geopolitical_analyzer import GeopoliticalAnalyzer
from topic_modeling import *
from lda_analysis import *

if __name__ == "__main__":
    print("📡 Fetching latest headlines...")
    headlines = get_rss_headlines()

    # Initialize analyzers
    event_analyzer = EventAnalyzer(time_window=60)
    geo_analyzer = GeopoliticalAnalyzer()

    # Step 2: Update both analyzers
    event_analyzer.update_data(headlines)
    geo_analyzer.process_headlines(headlines)

    # Step 3: Show top events
    print("\n🔍 Top Trending Events:")
    top_events = event_analyzer.get_top_events(16)
    for event, count in top_events.items():
        print(f"- {event} ({count} occurrences)")

    # Step 4: Forecast most frequent event
    if len(top_events) > 0:
        print(f"\n📈 Forecasting '{top_events.index[0]}'...")
        forecast = event_analyzer.forecast_event(top_events.index[0])
        print("\n🎯 Next 7-Day Forecast:")
        print(forecast)

    # Step 5: Run LDA Topic Modeling
    print("\n🧠 Running LDA Topic Modeling...")
    lda_model, tfidf_vectorizer, X = train_lda_model(headlines, n_topics=16)
    topic_assignments = get_topic_assignments(lda_model, tfidf_vectorizer, headlines)

    # Plot top words per topic
    print_top_words(lda_model, tfidf_vectorizer.get_feature_names_out())

    # Plot topic distribution
    plot_topic_distribution(headlines, topic_assignments)

    # Visualize topics in 2D
    visualize_topics_with_tsne(lda_model, tfidf_vectorizer, headlines, topic_assignments=topic_assignments)

    # Step 6: Visualize geopolitical relationships
    print("\n🌍 Visualizing country relationships:")
    geo_analyzer.visualize_relationships(min_weight=1)

    print("\n🕸️ Visualizing entity network:")
    geo_analyzer.visualize_entity_network()
