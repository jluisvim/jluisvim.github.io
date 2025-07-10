# rss_fetcher.py
import feedparser
from datetime import datetime, timedelta
import pytz

def get_rss_headlines(max_articles=50):
    FEEDS = {
        "BBC": "http://feeds.bbci.co.uk/news/rss.xml",
        "Yahoo": "https://www.yahoo.com/news/rss ",
        "LATimes": "https://www.latimes.com/local/rss2.0.xml ",
        "The Guardian (MX)": "https://www.theguardian.com/world/mexico/rss ",
        "SCMP": "https://www.scmp.com/rss/5/feed/ ",
        "Al Jazeera": "https://www.aljazeera.com/xml/rss/all.xml ",
        "Brasil Wire": "https://www.brasilwire.com/feed/",
        "France 24": "https://www.france24.com/en/france/rss",
        "Hong Kong Press": "https://hongkongfp.com/feed/",
    }

    headlines = []
    UTC = pytz.UTC
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
                    "raw": entry
                })
        except Exception as e:
            print(f"⚠️ Failed to fetch {source}: {str(e)}")
    return sorted(headlines, key=lambda x: x["date"])
