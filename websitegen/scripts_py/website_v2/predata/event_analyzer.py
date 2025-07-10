# event_analyzer.py
from nlp_utils import analyze_text
import pandas as pd
from statsmodels.tsa.arima.model import ARIMA
import matplotlib.pyplot as plt

class EventAnalyzer:
    def __init__(self, time_window=30):
        self.time_window = time_window
        self.historical_data = pd.DataFrame()

    def update_data(self, headlines):
        event_records = []
        for article in headlines:
            analysis = analyze_text(article["title"])
            date = article["date"]
            for event in analysis["events"]:
                event_records.append({
                    "date": date,
                    "event": event["lemma"],
                    "count": 1,
                    "context": event["context"]
                })
            for rel in analysis["relationships"]:
                event_records.append({
                    "date": date,
                    "event": f"{rel['subject']}_{rel['lemma']}_{rel['object']}",
                    "count": 1,
                    "context": f"{rel['subject']} {rel['verb']} {rel['object']}"
                })
        new_data = pd.DataFrame(event_records)
        if not new_data.empty:
            new_data = new_data.groupby(['date', 'event']).agg({'count': 'sum', 'context': 'first'})
            self.historical_data = pd.concat([self.historical_data, new_data]).groupby(['date', 'event']).sum()

    def get_top_events(self, n=8):
        return self.historical_data.groupby('event')['count'].sum().nlargest(n)

    def forecast_event(self, event_name, forecast_days=7):
        if event_name not in self.historical_data.index.get_level_values('event'):
            raise ValueError(f"Event '{event_name}' not found")
        
        ts = self.historical_data.xs(event_name, level='event')['count']
        ts = ts.resample('D').sum().fillna(0)
        
        # Fix 1: Handle sparse data
        if len(ts) < 5:
            print(f"⚠️ Insufficient data ({len(ts)} points). Need at least 5 days.")
            return None
            
        # Fix 2: Add small constant to avoid division by zero
        ts = ts + 0.01
        
        # Check data quality
        if len(ts) < 5:
            print("🔴 Not enough data for forecasting")
        elif ts.var() < 0.1:  # Low variance
            print("🟠 Low variance - forecasts may be unreliable")
        else:
            print("🟢 Good data for forecasting")

        # Fix 3: Use simpler ARIMA model
        try:
            model = ARIMA(ts, order=(1,1,0))
            results = model.fit()
            forecast = results.get_forecast(steps=forecast_days)
            
            plt.figure(figsize=(12,6))
            ts.plot(label='Historical')
            forecast.predicted_mean.plot(label='Forecast')
            
            # Fix 4: Set proper x-axis limits
            x_min = ts.index.min() - pd.Timedelta(days=1)
            x_max = forecast.predicted_mean.index.max() + pd.Timedelta(days=1)
            plt.xlim(x_min, x_max)
            
            plt.title(f"Trend: '{event_name}'")
            plt.legend()
            plt.show()
            
            return forecast.predicted_mean
            
        except Exception as e:
            print(f"⚠️ Forecasting failed: {str(e)}")
            return None
