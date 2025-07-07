import pandas as pd
from bs4 import BeautifulSoup
import requests
from datetime import datetime, timedelta
from textblob import TextBlob
import numpy as np
import random
import os
from sklearn.ensemble import RandomForestClassifier
from prophet import Prophet

import matplotlib.pyplot as plt

# --- Configuration ---
COUNTRIES = ['Mexico', 'France', 'USA', 'Brazil', 'India', 'South Africa', 'China', 'Russia']
EVENT_TYPES = ['Protest', 'Riot', 'Strike', 'Violent clash', 'Demonstration']
NEWS_SOURCES = [
    ("BBC", "https://www.bbc.com/news/world", '.gs-c-promo-heading__title'),
    ("Reuters", "https://www.reuters.com/world/", '.text__text__1FZLe'),
    ("AP", "https://apnews.com/hub/world-news", '.PagePromo-title')
]

# --- Helper Functions ---
def get_current_date():
    return datetime.now().strftime('%Y-%m-%d')

def generate_synthetic_protests(days=60):
    """Generate realistic protest data for multiple countries"""
    data = []
    for i in range(days, 0, -1):
        date = datetime.now() - timedelta(days=i)
        for country in COUNTRIES:
            # More protests in some countries
            if random.random() < 0.3 if country in ['France', 'USA'] else 0.15:
                event = random.choice(EVENT_TYPES)
                fatalities = int(np.random.poisson(3 if event in ['Riot', 'Violent clash'] else 0.5))
                data.append({
                    'country': country,
                    'event_type': event,
                    'fatalities': fatalities,
                    'date': date.strftime('%Y-%m-%d')
                })
    return pd.DataFrame(data)

# --- Data Collection ---
def scrape_news():
    """Try multiple news sources until success"""
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    
    for name, url, selector in NEWS_SOURCES:
        try:
            print(f"Attempting to scrape {name}...")
            response = requests.get(url, headers=headers, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')
            headlines = [h.text.strip() for h in soup.select(selector) if h.text.strip()]
            
            if headlines:
                print(f"✓ Successfully scraped {len(headlines)} headlines from {name}")
                return headlines[:10]  # Return max 10 headlines
            
        except Exception as e:
            print(f"⚠️ Failed to scrape {name}: {str(e)[:50]}...")
    
    # Fallback headlines
    fallback = [
        "Global leaders meet to address economic crisis",
        "Climate activists stage worldwide protests",
        "Trade tensions rise between major powers",
        "Government announces new social reforms",
        "UN calls for peaceful resolution to conflicts"
    ]
    print("⚠️ Using fallback headlines")
    return fallback

def load_protest_data():
    """Load protest data with multiple fallback options"""
    # Try local CSV first
    if os.path.exists("protest_data.csv"):
        try:
            df = pd.read_csv("protest_data.csv")
            if not df.empty:
                print("✓ Loaded protest data from local file")
                return df
        except Exception as e:
            print(f"⚠️ Error reading local file: {e}")
    
    # Generate synthetic data
    print("⚠️ Generating realistic synthetic protest data")
    return generate_synthetic_protests()

# --- Analysis ---
def analyze_headlines(headlines):
    """Perform sentiment analysis on headlines"""
    if not headlines:
        return 0, []
    
    sentiments = []
    analyzed = []
    for h in headlines:
        blob = TextBlob(h)
        sentiments.append(blob.sentiment.polarity)
        analyzed.append(f"{h} (Sentiment: {blob.sentiment.polarity:.2f})")
    
    return np.mean(sentiments), analyzed

def calculate_protest_metrics(protests):
    """Calculate key protest statistics"""
    protests = protests.copy()
    protests['date'] = pd.to_datetime(protests['date'])
    
    last_30_days = protests[protests['date'] > (datetime.now() - timedelta(days=30))]
    
    metrics = {
        'total_events': len(last_30_days),
        'total_fatalities': last_30_days['fatalities'].sum(),
        'most_active_country': last_30_days['country'].mode()[0] if not last_30_days.empty else "N/A",
        'most_common_event': last_30_days['event_type'].mode()[0] if not last_30_days.empty else "N/A"
    }
    
    return metrics

# --- Prediction Models ---
class RiskModel:
    def __init__(self):
        # Simulate trained model
        self.model = RandomForestClassifier()
        
        # Simulated training data
        X_train = [
            [-0.8, 15, 5.0],  # High risk
            [0.5, 2, 0.5],    # Low risk
            [-0.3, 8, 2.0]    # Medium risk
        ]
        y_train = [2, 0, 1]
        self.model.fit(X_train, y_train)
    
    def predict_risk(self, avg_sentiment, protest_count, avg_fatalities):
        prediction = self.model.predict([[avg_sentiment, protest_count, avg_fatalities]])[0]
        return {0: 'Low', 1: 'Medium', 2: 'High'}[prediction]

def generate_forecast(protests):
    """Generate protest forecast using Prophet"""
    try:
        # Prepare time series data
        ts_data = protests.copy()
        ts_data['date'] = pd.to_datetime(ts_data['date'])
        ts_data = ts_data.set_index('date').resample('D')['fatalities'].sum().reset_index()
        ts_data.columns = ['ds', 'y']
        
        if len(ts_data) < 14:
            raise ValueError("Insufficient historical data")
        
        model = Prophet()
        model.fit(ts_data)
        
        future = model.make_future_dataframe(periods=30)
        forecast = model.predict(future)
        
        return forecast[['ds', 'yhat']].tail(30)
    
    except Exception as e:
        print(f"⚠️ Forecast error: {str(e)[:100]}")
        return None


# [Previous code remains the same until main()]

def main():
    print("\n🌍 Geopolitical Risk Assessment System")
    print("🔄 Collecting and analyzing data...")
    
    # Data collection
    headlines = scrape_news()
    protests = load_protest_data()
    
    # Analysis
    avg_sentiment, analyzed_headlines = analyze_headlines(headlines)
    protest_metrics = calculate_protest_metrics(protests)
    
    # Risk prediction
    risk_model = RiskModel()
    risk_level = risk_model.predict_risk(
        avg_sentiment,
        protest_metrics['total_events'],
        protest_metrics['total_fatalities'] / max(1, protest_metrics['total_events'])
    )
    
    # Forecast
    forecast = generate_forecast(protests)
    
    # Output results
    print("\n📰 Latest Headlines Analysis:")
    for i, h in enumerate(analyzed_headlines[:5], 1):
        print(f"{i}. {h}")
    
    print("\n📊 Protest Metrics (Last 30 Days):")
    print(f"• Total Events: {protest_metrics['total_events']}")
    print(f"• Total Fatalities: {protest_metrics['total_fatalities']}")
    print(f"• Most Active Country: {protest_metrics['most_active_country']}")
    print(f"• Most Common Event Type: {protest_metrics['most_common_event']}")
    
    print(f"\n🔴 Risk Assessment: {risk_level}")
    
    print("\n🔮 30-Day Protest Forecast:")
    if forecast is not None:
        print(forecast.tail(5).to_string(index=False))
        
        # Generate plot
        plt.figure(figsize=(10, 5))
        plt.plot(forecast['ds'], forecast['yhat'], label='Predicted')
        if 'yhat_lower' in forecast.columns:
            plt.fill_between(forecast['ds'], forecast['yhat_lower'], forecast['yhat_upper'], alpha=0.2)
        plt.title("30-Day Protest Fatality Forecast")
        plt.xlabel("Date")
        plt.ylabel("Expected Fatalities")
        plt.legend()
        plt.savefig("forecast.png")
        print("\n✓ Forecast plot saved as forecast.png")
    else:
        print("Forecast unavailable - insufficient historical data")
    
    print("\n✅ Analysis complete")

if __name__ == "__main__":
    main()
