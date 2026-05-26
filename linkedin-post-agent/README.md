# LinkedIn Post Generator Agent

An AI-powered agent that generates LinkedIn posts based on trending topics, with a beautiful web UI for easy content creation and refinement.

## Features

- 🔍 **Trend Lookup**: Fetches trending topics from Google Trends and industry keywords
- ✍️ **AI Post Generation**: Creates drafts matching your writing style using Ollama LLM
- 🎨 **Beautiful Web UI**: Modern, interactive interface with Tailwind CSS
- 💬 **Iterative Refinement**: Chat-style refinement - ask AI to edit, add, or modify content
- 👀 **Review Workflow**: Organize drafts, approve, and batch-post
- 🚀 **Auto Posting**: Publishes approved posts via browser automation

## Quick Start

### 1. Setup

```bash
cd E:\Ollama\Agents\linkedin-post-agent
setup.bat
```

### 2. Configure

```bash
copy .env.example .env
```

Edit `.env` with:
- Your LinkedIn email/password
- Ollama settings (default: `http://localhost:11434`)

### 3. Start Ollama

```bash
ollama serve
ollama pull llama3.2
```

### 4. Launch Web UI

```bash
run-webui.bat
```

Then open **http://localhost:8000** in your browser.

## Web UI Features

### Trending Topics Tab
- View trending topics from Google Trends
- Click any trend to use it for post generation
- See suggested content angles

### Generate Post Tab
- Enter a topic or use quick-start suggestions
- Choose content angle (personal, misconception, prediction, story)
- Real-time post generation with character count
- **Refinement Chat**: Ask AI to modify the draft:
  - "Make it shorter"
  - "Add more emojis"
  - "More professional tone"
  - "Add a call-to-action"
  - "Make it more engaging"

### My Drafts Tab
- View all saved drafts
- Edit content manually
- Approve drafts for posting
- Post directly to LinkedIn
- Delete unwanted drafts

### My Style Tab
- Analyze your writing style from past posts
- Save your tone, length, and structure preferences
- Future posts will match your unique voice

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/trends` | Fetch trending topics |
| POST | `/api/generate` | Generate a new post |
| POST | `/api/refine` | Refine an existing draft |
| GET | `/api/drafts` | List all drafts |
| GET | `/api/drafts/{id}` | Get a specific draft |
| PUT | `/api/drafts/{id}` | Update draft content |
| DELETE | `/api/drafts/{id}` | Delete a draft |
| POST | `/api/drafts/{id}/review` | Mark draft as reviewed |
| POST | `/api/post/{id}` | Post to LinkedIn |
| POST | `/api/analyze-style` | Analyze writing style |

## Project Structure

```
linkedin-post-agent/
├── static/
│   ├── index.html      # Web UI (Tailwind CSS)
│   └── app.js          # Frontend JavaScript
├── server.py           # FastAPI backend
├── main.py             # CLI interface
├── config.py           # Configuration
├── llm.py              # Ollama LLM client
├── trends.py           # Trend fetching
├── generator.py        # Post generation
├── linkedin.py         # LinkedIn automation
├── requirements.txt    # Dependencies
├── .env.example        # Environment template
├── setup.bat           # Setup script
├── run-webui.bat       # Launch web UI
└── run.bat             # Launch CLI
```

## Refinement Examples

Once a post is generated, you can refine it with natural language:

| Instruction | Effect |
|-------------|--------|
| "Make it shorter" | Reduces length while keeping key points |
| "Add emojis" | Inserts relevant emojis throughout |
| "More professional" | Adjusts tone to be more formal |
| "Add hashtags" | Appends relevant hashtags |
| "Make it punchier" | Stronger hook, more engaging opening |
| "Add a question" | Includes a thought-provoking question |
| "Less salesy" | Removes promotional language |

## Troubleshooting

**Ollama not connecting:**
- Ensure Ollama is running: `ollama serve`
- Check model is installed: `ollama list`
- Install model: `ollama pull llama3.2`

**LinkedIn posting fails:**
- Verify credentials in `.env`
- Browser automation requires visible browser (not headless)
- Session saved after first login

**Port 8000 in use:**
- Change port in `run-webui.bat`: `--port 8001`
