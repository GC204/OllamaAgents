"""Configuration settings for LinkedIn Post Generator Agent."""

from pathlib import Path
from dotenv import load_dotenv
import os

load_dotenv()

# Base directories
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
DRAFTS_DIR = BASE_DIR / "drafts"

# Create directories if they don't exist
DATA_DIR.mkdir(exist_ok=True)
DRAFTS_DIR.mkdir(exist_ok=True)

# LinkedIn credentials
LINKEDIN_EMAIL = os.getenv("LINKEDIN_EMAIL", "")
LINKEDIN_PASSWORD = os.getenv("LINKEDIN_PASSWORD", "")

# Ollama configuration
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")

# Post generation settings
POST_SETTINGS = {
    "max_length": 1300,  # LinkedIn character limit is 3000, but shorter performs better
    "min_length": 150,
    "include_hashtags": True,
    "max_hashtags": 5,
    "include_emoji": False,
    "tone": "professional",  # professional, casual, enthusiastic, thought-leader
}

# Trend sources
TREND_SOURCES = {
    "linkedin_feed": True,
    "google_trends": True,
    "industry_keywords": [
        "artificial intelligence",
        "machine learning",
        "career development",
        "leadership",
        "innovation",
        "technology trends",
        "workplace culture",
        "digital transformation",
    ],
}

# Posting schedule (24h format)
POSTING_SCHEDULE = {
    "preferred_hours": [9, 10, 11, 14, 15],  # Best engagement times
    "timezone": "UTC",
}
