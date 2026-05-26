# LinkedIn Post Generator Agent

## Project Structure

```
linkedin-post-agent/
├── main.py           # CLI interface with Rich UI
├── config.py         # Configuration and settings
├── llm.py            # Ollama LLM client
├── trends.py         # Trend fetching (Google Trends, industry keywords)
├── generator.py      # Post generation and draft management
├── linkedin.py       # LinkedIn browser automation (Playwright)
├── requirements.txt  # Python dependencies
├── .env.example      # Environment template
├── setup.bat         # Windows setup script
└── run.bat           # Quick run script
```

## Quick Start

1. Run `setup.bat` to install dependencies
2. Copy `.env.example` to `.env` and add LinkedIn credentials
3. Ensure Ollama is running: `ollama serve`
4. Install a model: `ollama pull llama3.2`
5. Run: `python main.py` or `run.bat`

## Architecture

- **TrendFetcher**: Fetches trends from Google Trends RSS and industry keywords
- **PostGenerator**: Generates posts using Ollama LLM with style matching
- **LinkedInBrowser**: Playwright-based automation for login and posting
- **Style Profile**: Learns user's writing style from sample posts

## Key Files

- `data/style_profile.json` - User's writing style (auto-generated)
- `data/linkedin_session.json` - Saved browser session cookies
- `drafts/draft_*.json` - Generated post drafts
