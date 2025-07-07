import feedparser
import stanza
from collections import defaultdict
from urllib.request import urlopen
from bs4 import BeautifulSoup  # For parsing Reuters HTML if needed
import pandas as pd
from prophet import Prophet
import matplotlib.pyplot as plt
import networkx as nx
from datetime import datetime, timedelta
from statsmodels.tsa.arima.model import ARIMA
import pytz
# [Previous imports remain the same]
import pycountry  # Add this import
import os

# Initialize Stanza NLP
print("Loading NLP model...")
if not os.path.isdir('/home/jluis/stanza_resources'):
    print('Downloading Stanza resources...')
    stanza.download("en")

nlp = stanza.Pipeline(lang="en", processors="tokenize,ner,pos,lemma,depparse", use_gpu=False)

# RSS Feed URLs
FEEDS = {
    "BBC": "http://feeds.bbci.co.uk/news/rss.xml",
    "Yahoo": "https://www.yahoo.com/news/rss",
    "LATimes": "https://www.latimes.com/local/rss2.0.xml",
    "The Guardian (MX)": "https://www.theguardian.com/world/mexico/rss",
    "SCMP": "https://www.scmp.com/rss/5/feed/",
    "Al Jazeera": "https://www.aljazeera.com/xml/rss/all.xml",
#     "Politico": "http://www.politico.com/rss/politicopicks.xml",
#     "Reuters Top": "http://feeds.reuters.com/reuters/topNews",  # Main headlines
#     "Reuters World": "http://feeds.reuters.com/Reuters/worldNews",  # World-specific
}

# Timezone normalization
UTC = pytz.UTC

def get_rss_headlines(max_articles=30):
    """Fetch headlines with timestamps from all feeds"""
    headlines = []
    for source, url in FEEDS.items():
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:max_articles]:
                date = entry.get('published_parsed', entry.get('updated_parsed', None))
                date = datetime(*date[:6]).replace(tzinfo=UTC) if date else datetime.now(UTC)
                
                headlines.append({
                    "source": source,
                    "title": entry.title,
                    "link": entry.link,
                    "date": date,
                    "raw": entry  # Keep raw entry for debugging
                })
        except Exception as e:
            print(f"⚠️ Failed to fetch {source}: {str(e)}")
    return sorted(headlines, key=lambda x: x["date"])

# NLP Analysis Functions
def analyze_text(text):
    doc = nlp(text)
    return {
        "entities": extract_entities(doc),
        "relationships": extract_relationships(doc),
        "events": extract_events(doc)
    }

def extract_entities(doc):
    return [(ent.text, ent.type) for sent in doc.sentences for ent in sent.ents]

def extract_relationships(doc):
    relationships = []
    for sent in doc.sentences:
        verbs = [word for word in sent.words if word.upos == "VERB"]
        for verb in verbs:
            subj = [word.text for word in sent.words if word.head == verb.id and word.deprel in ("nsubj", "nsubj:pass")]
            obj = [word.text for word in sent.words if word.head == verb.id and word.deprel in ("obj", "dobj")]
            if subj and obj:
                relationships.append({
                    "subject": " ".join(subj),
                    "verb": verb.text,
                    "object": " ".join(obj),
                    "lemma": verb.lemma
                })
    return relationships

def extract_events(doc):
    events = []
    for sent in doc.sentences:
        for word in sent.words:
            if word.upos == "VERB":
                context_words = [w.text for w in sent.words[max(0,word.id-2):word.id+3]]
                events.append({
                    "text": word.text,
                    "lemma": word.lemma,
                    "context": " ".join(context_words)
                })
    return events

# Trend Analysis Module
class EventAnalyzer:
    def __init__(self, time_window=30):
        self.time_window = time_window
        self.historical_data = pd.DataFrame()
        
    def update_data(self, headlines):
        """Process new headlines and update historical data"""
        event_records = []
        
        for article in headlines:
            analysis = analyze_text(article["title"])
            date = article["date"]
            
            # Count all events
            for event in analysis["events"]:
                event_records.append({
                    "date": date,
                    "event": event["lemma"],
                    "count": 1,
                    "context": event["context"]
                })
            
            # Count relationships
            for rel in analysis["relationships"]:
                event_records.append({
                    "date": date,
                    "event": f"{rel['subject']}_{rel['lemma']}_{rel['object']}",
                    "count": 1,
                    "context": f"{rel['subject']} {rel['verb']} {rel['object']}"
                })
        
        # Update historical data
        new_data = pd.DataFrame(event_records)
        if not new_data.empty:
            new_data = new_data.groupby(['date', 'event']).agg({'count':'sum', 'context':'first'})
            self.historical_data = pd.concat([self.historical_data, new_data]).groupby(['date', 'event']).sum()
    
    def get_top_events(self, n=5):
        """Get most frequent events"""
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


# [Keep all existing functions and classes until the EventAnalyzer class]

class GeopoliticalAnalyzer:
    def __init__(self):
        self.country_data = defaultdict(lambda: pd.DataFrame())
        self.relationship_graph = nx.DiGraph()
        self.entity_graph = nx.Graph()
        
    def process_headlines(self, headlines):
        for article in headlines:
            doc = nlp(article["title"])
            date = article["date"]
            
            # Extract entities and relationships
            entities = self._extract_entities(doc)
            relationships = self._extract_relationships(doc)
            
            # Update country-specific data
            self._update_country_data(entities, relationships, date)
            
            # Update relationship graphs
            self._update_relationship_graph(entities, relationships)
            self._update_entity_graph(entities, relationships)
    
    def _extract_entities(self, doc):
        entities = []
        for ent in doc.ents:
            if ent.type in ["GPE", "ORG", "PERSON"]:
                norm_name = self._normalize_entity(ent.text, ent.type)
                entities.append((norm_name, ent.type))
        return entities
    
    def _extract_relationships(self, doc):
        relationships = []
        for sent in doc.sentences:
            for word in sent.words:
                if word.upos == "VERB":
                    subj = [w for w in sent.words if w.head == word.id and w.deprel in ("nsubj", "nsubj:pass")]
                    obj = [w for w in sent.words if w.head == word.id and w.deprel in ("obj", "dobj")]
                    if subj and obj:
                        relationships.append({
                            "subject": subj[0].text,
                            "verb": word.lemma,
                            "object": obj[0].text
                        })
        return relationships
    
    def _normalize_entity(self, name, ent_type):
        """Convert country names to codes, standardize org names"""
        if ent_type == "GPE":
            try:
                return pycountry.countries.lookup(name).alpha_3
            except:
                return name
        return name.lower().strip()
    
    def _update_country_data(self, entities, relationships, date):
        countries = {e[0] for e in entities if len(e[0]) == 3}  # ISO3 codes
        
        for country in countries:
            for rel in relationships:
                if rel["subject"] == country or rel["object"] == country:
                    record = {
                        "date": date,
                        "event": rel["verb"],
                        "count": 1,
                        "target": rel["object"] if rel["subject"] == country else rel["subject"]
                    }
                    self.country_data[country] = pd.concat([
                        self.country_data[country],
                        pd.DataFrame([record])
                    ])
    
    def _update_relationship_graph(self, entities, relationships):
        for rel in relationships:
            subj = self._normalize_entity(rel["subject"], "GPE")
            obj = self._normalize_entity(rel["object"], "GPE")
            
            if subj != obj:
                if self.relationship_graph.has_edge(subj, obj):
                    self.relationship_graph[subj][obj]["weight"] += 1
                    self.relationship_graph[subj][obj]["verbs"].add(rel["verb"])
                else:
                    self.relationship_graph.add_edge(
                        subj, obj, 
                        weight=1, 
                        verbs={rel["verb"]},
                        type="country_relation"
                    )
    
    def _update_entity_graph(self, entities, relationships):
        for ent, ent_type in entities:
            self.entity_graph.add_node(ent, type=ent_type)
            
        for rel in relationships:
            subj = self._normalize_entity(rel["subject"], "GPE")
            obj = self._normalize_entity(rel["object"], "GPE")
            if subj in self.entity_graph and obj in self.entity_graph:
                self.entity_graph.add_edge(subj, obj, verb=rel["verb"])

    def visualize_relationships(self, min_weight=2):
        """Create a directed graph of country relationships"""
        plt.figure(figsize=(15, 10))
        
        # Filter edges by weight
        edges = [(u, v) for (u, v, d) in self.relationship_graph.edges(data=True) 
                if d["weight"] >= min_weight]
        
        # Node positions
        pos = nx.spring_layout(self.relationship_graph)
        
        # Draw nodes
        nx.draw_networkx_nodes(
            self.relationship_graph, pos,
            node_size=500,
            node_color="lightblue"
        )
        
        # Draw edges
        nx.draw_networkx_edges(
            self.relationship_graph, pos,
            edgelist=edges,
            width=[d["weight"]*0.5 for (u,v,d) in self.relationship_graph.edges(data=True) 
                  if (u,v) in edges],
            edge_color="gray",
            arrowsize=20
        )
        
        # Edge labels (verbs)
        edge_labels = {
            (u, v): ", ".join(d["verbs"])[:15] + "..."
            for u, v, d in self.relationship_graph.edges(data=True)
            if (u,v) in edges
        }
        nx.draw_networkx_edge_labels(
            self.relationship_graph, pos,
            edge_labels=edge_labels,
            font_size=8
        )
        
        # Node labels
        nx.draw_networkx_labels(
            self.relationship_graph, pos,
            font_size=10,
            font_weight="bold"
        )
        
        plt.title("Geopolitical Relationship Network")
        plt.axis("off")
        plt.tight_layout()
        plt.show()
    
    def visualize_entity_network(self):
        """Show entities and their connections"""
        plt.figure(figsize=(15, 10))
        
        # Color nodes by type
        node_colors = []
        for node in self.entity_graph.nodes():
            if len(node) == 3:  # Country code
                node_colors.append("lightblue")
            elif self.entity_graph.nodes[node]["type"] == "ORG":
                node_colors.append("lightgreen")
            else:
                node_colors.append("pink")
        
        pos = nx.spring_layout(self.entity_graph)
        nx.draw(
            self.entity_graph, pos,
            with_labels=True,
            node_size=500,
            node_color=node_colors,
            font_size=8,
            edge_color="gray"
        )
        
        plt.title("Entity Relationship Network")
        plt.axis("off")
        plt.show()

# Main Execution
if __name__ == "__main__":
    # Initialize analyzers
    event_analyzer = EventAnalyzer(time_window=60)
    geo_analyzer = GeopoliticalAnalyzer()
    
    # Step 1: Fetch and analyze current headlines
    print("📡 Fetching latest headlines...")
    headlines = get_rss_headlines()
    
    # Step 2: Update both analyzers
    event_analyzer.update_data(headlines)
    geo_analyzer.process_headlines(headlines)
    
    # Step 3: Show top events
    print("\n🔍 Top Trending Events:")
    top_events = event_analyzer.get_top_events(6)
    for event, count in top_events.items():
        print(f"- {event} ({count} occurrences)")
    
    # Step 4: Forecast most frequent event
    if len(top_events) > 0:
        print(f"\n📈 Forecasting '{top_events.index[0]}'...")
        forecast = event_analyzer.forecast_event(top_events.index[0])
        print("\n🎯 Next 7-Day Forecast:")
        print(forecast)
    
    # Step 5: Show geopolitical relationships
    print("\n🌍 Visualizing country relationships:")
    geo_analyzer.visualize_relationships(min_weight=1)
    
    print("\n🕸️ Visualizing entity network:")
    geo_analyzer.visualize_entity_network()
