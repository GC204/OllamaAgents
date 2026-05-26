"""Trend fetching module for LinkedIn post generation."""

import requests
from typing import List, Dict
from datetime import datetime
from bs4 import BeautifulSoup
from config import TREND_SOURCES
import json
from pathlib import Path


class TrendFetcher:
    """Fetches trending topics from various sources."""

    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

    def fetch_google_trends(self, geo: str = "US", limit: int = 10) -> List[Dict]:
        """Fetch trending topics from Google Trends."""
        try:
            # Using Google Trends RSS feed approach
            url = f"https://trends.google.com/trends/trendingsearches/daily/rss?geo={geo}"
            response = requests.get(url, headers=self.headers, timeout=10)

            if response.status_code != 200:
                return []

            soup = BeautifulSoup(response.content, "lxml")
            items = soup.find_all("item")

            trends = []
            for item in items[:limit]:
                title = item.find("title")
                desc = item.find("description")
                if title:
                    trends.append({
                        "source": "google_trends",
                        "topic": title.text.strip(),
                        "description": desc.text.strip() if desc else "",
                        "fetched_at": datetime.now().isoformat(),
                    })
            return trends
        except Exception as e:
            print(f"Error fetching Google Trends: {e}")
            return []

    def fetch_industry_trends(self, keywords: List[str]) -> List[Dict]:
        """Generate trend suggestions based on industry keywords."""
        trends = []
        for keyword in keywords:
            trends.append({
                "source": "industry_keyword",
                "topic": keyword,
                "description": f"Trending topic in {keyword}",
                "fetched_at": datetime.now().isoformat(),
                "suggested_angles": self._suggest_angles(keyword),
            })
        return trends

    def _suggest_angles(self, topic: str) -> List[str]:
        """Suggest content angles for a topic."""
        angles = [
            f"Share a recent learning or insight about {topic}",
            f"Discuss a common misconception about {topic}",
            f"Predict the future of {topic}",
            f"Share a personal experience related to {topic}",
            f"Explain {topic} to someone new to the field",
            f"Compare old vs new approaches in {topic}",
        ]
        return angles

    def fetch_linkedin_feed_trends(self) -> List[Dict]:
        """
        Fetch trending content from LinkedIn feed.
        Note: This requires an authenticated session from LinkedInBrowser.
        For now, returns placeholder suggestions.
        """
        # This would require LinkedIn session cookies
        # Implemented in conjunction with LinkedInBrowser
        return []

    def get_trending_topics(self, limit: int = 15) -> List[Dict]:
        """Get combined trending topics from all sources."""
        all_trends = []

        # Fetch from Google Trends
        if TREND_SOURCES.get("google_trends", True):
            google_trends = self.fetch_google_trends()
            all_trends.extend(google_trends)

        # Fetch from industry keywords
        if TREND_SOURCES.get("industry_keywords", []):
            industry_trends = self.fetch_industry_trends(
                TREND_SOURCES["industry_keywords"]
            )
            all_trends.extend(industry_trends)

        # Deduplicate by topic
        seen = set()
        unique_trends = []
        for trend in all_trends:
            topic_key = trend["topic"].lower()
            if topic_key not in seen:
                seen.add(topic_key)
                unique_trends.append(trend)

        return unique_trends[:limit]

    def save_trends(self, trends: List[Dict], filepath: str = None) -> str:
        """Save trends to a JSON file."""
        if filepath is None:
            from config import DATA_DIR
            filepath = DATA_DIR / f"trends_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(trends, f, indent=2)

        return str(filepath)

    def load_saved_trends(self, filepath: str = None) -> List[Dict]:
        """Load trends from a saved JSON file."""
        if filepath is None:
            from config import DATA_DIR
            # Load most recent trends file
            trends_files = list(DATA_DIR.glob("trends_*.json"))
            if trends_files:
                filepath = max(trends_files, key=lambda p: p.stat().st_mtime)
            else:
                return []

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []


# Global instance
trend_fetcher = TrendFetcher()
