# DevOps CI/CD Agent

An AI-powered agent for automatically generating GitHub Actions CI/CD pipelines. The agent analyzes your repository's codebase, understands your requirements through a chat interface, and generates customized CI/CD YAML files.

## Implementation Progress ✅

### Phase 1 - Complete ✅
**Backend Foundation & GitHub Integration**

- ✅ Project structure with organized backend/frontend directories
- ✅ SQLAlchemy ORM models (Sessions, ChatMessages, GeneratedCI)
- ✅ FastAPI application with CORS support
- ✅ GitHub integration: `GitHubManager` for auth, cloning, PR operations
- ✅ Ollama LLM client for text generation
- ✅ Session management CRUD endpoints
- ✅ RESTful API architecture

### Phase 2 - Complete ✅
**Codebase Analysis & Detection**

- ✅ Fast detector (language/framework identification via file scanning)
- ✅ Deep detector (dependency parsing, architecture pattern detection)
- ✅ Codebase analyzer orchestrator
- ✅ CI recommendation engine based on detected stack
- ✅ Analysis API routes (`/analyze`, `/quick-analyze`)
- ✅ Support for: Python, JavaScript/TypeScript, Java, Go, Rust, C#, Ruby, PHP

### Phase 3 - Complete ✅
**LLM Integration & CI Generation**

- ✅ Prompt templates for stack analysis and CI generation
- ✅ `CIGenerator` service with Ollama integration
- ✅ YAML validation and error correction
- ✅ Multi-turn chat routes for requirements gathering
- ✅ AI-powered CI generation (`generate-ci` endpoint)
- ✅ Fallback CI templates for reliability
- ✅ Safety checks (no hardcoded secrets, proper YAML syntax)

### Phase 4 - Complete ✅
**GitHub PR Creation & Approval Flows**

- ✅ `PRCreator` service for PR management
- ✅ Automated feature branch creation
- ✅ CI/CD YAML file commit to branch
- ✅ Pull request generation with descriptions
- ✅ Dual approval workflows:
  - GitHub-direct: User approves on GitHub, agent merges
  - Chat-based: User reviews diff in chat, confirms in interface
- ✅ PR status tracking and diff previews
- ✅ Automatic status updates in database

### Complete API Endpoints

**Sessions**:
- `POST /api/sessions` - Create new session with repo
- `GET /api/sessions/{id}` - Fetch session details
- `GET /api/sessions` - List all sessions
- `DELETE /api/sessions/{id}` - Complete/delete session

**Analysis**:
- `POST /api/sessions/{id}/analyze` - Full codebase analysis (deep=true/false)
- `POST /api/sessions/{id}/quick-analyze` - Fast stack detection

**Chat**:
- `POST /api/sessions/{id}/chat` - Add chat message
- `GET /api/sessions/{id}/chat` - Get chat history
- `POST /api/sessions/{id}/ai-response` - Get AI response
- `POST /api/sessions/{id}/generate-ci` - Generate CI workflow

**CI/CD & PRs**:
- `POST /api/sessions/{id}/ci/{ci_id}/create-pr` - Create pull request
- `GET /api/sessions/{id}/ci/{ci_id}/pr-status` - Get PR status
- `GET /api/sessions/{id}/ci/{ci_id}/pr-diff` - View PR diff
- `POST /api/sessions/{id}/ci/{ci_id}/approve-github` - Merge PR (GitHub-direct)
- `POST /api/sessions/{id}/ci/{ci_id}/approve-chat` - Merge PR (chat-based)

**Health**:
- `GET /health` - Health check
- `GET /` - API info

### Database Schema

**Sessions Table**:
- `id` (UUID, primary key)
- `repo_name` (string, required)
- `repo_url` (string, optional)
- `release_branch` (string, optional)
- `user_input` (text, optional)
- `status` (enum: ACTIVE, COMPLETED, FAILED)
- `created_at`, `updated_at` (timestamps)

**ChatMessages Table**:
- `id` (UUID, primary key)
- `session_id` (FK to sessions)
- `role` (enum: USER, ASSISTANT, SYSTEM)
- `content` (text)
- `created_at` (timestamp)

**GeneratedCI Table**:
- `id` (UUID, primary key)
- `session_id` (FK to sessions)
- `repo_name`, `branch` (strings)
- `yaml_content` (text)
- `pr_url`, `pr_number` (strings)
- `status` (enum: PENDING, GENERATED, PR_CREATED, APPROVED, MERGED, FAILED)
- `approval_timestamp`, `merge_timestamp` (timestamps)
- `error_message` (text)

## Setup Instructions

### Prerequisites

- Python 3.10+
- Ollama running on localhost:11434 (running Gemma 4 model)
- GitHub Personal Access Token with repo write + workflow permissions

### Installation

1. **Copy environment template**:
   ```bash
   cd e:\Ollama\Agents\DevOpsAgent
   copy .env.example .env
   ```

2. **Configure .env**:
   ```bash
   # Add your GitHub PAT token
   GITHUB_PAT_TOKEN=your_github_pat_here
   
   # Other settings should work with defaults
   ```

3. **Create virtual environment** (recommended):
   ```bash
   python -m venv venv
   .\venv\Scripts\activate  # On Windows
   ```

4. **Install dependencies**:
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

### Running the Backend

From the `backend` directory with virtual environment activated:

```bash
# Start FastAPI server
python -m uvicorn app:app --reload --host 127.0.0.1 --port 8000
```

Server will be available at: `http://localhost:8000`

### Testing Phase 1

**1. Health Check**:
```bash
curl http://localhost:8000/health
```

Expected output:
```json
{"status": "healthy"}
```

**2. Create a Session**:
```bash
curl -X POST http://localhost:8000/api/sessions \
  -H "Content-Type: application/json" \
  -d '{
    "repo_name": "owner/repo-name",
    "release_branch": "main",
    "user_input": "Generate CI for Python + React project"
  }'
```

**3. Fetch Session**:
```bash
curl http://localhost:8000/api/sessions/{session_id}
```

**4. Add Chat Message**:
```bash
curl -X POST http://localhost:8000/api/sessions/{session_id}/chat \
  -H "Content-Type: application/json" \
  -d '{
    "role": "user",
    "content": "I want to test on Python 3.9 and 3.10"
  }'
```

**5. Get Chat History**:
```bash
curl http://localhost:8000/api/sessions/{session_id}/chat
```

## Verification Checklist for Phase 1

- ✅ FastAPI server starts without errors
- ✅ SQLite database created in `data/devops_agent.db`
- ✅ CORS configured for frontend communication
- ✅ GitHub authentication works with PAT token
- ✅ Repository lookup works (returns 404 for non-existent repos)
- ✅ Session CRUD operations functional
- ✅ Chat message storage working
- ✅ Ollama client connects to local server
- ✅ Model listing works (`ollama_client.list_models()`)

## Environment Variables Reference

| Variable | Default | Purpose |
|----------|---------|---------|
| `GITHUB_PAT_TOKEN` | Required | GitHub Personal Access Token |
| `OLLAMA_HOST` | localhost | Ollama server hostname |
| `OLLAMA_PORT` | 11434 | Ollama server port |
| `OLLAMA_MODEL` | gemma4 | Model name to use |
| `BACKEND_HOST` | 127.0.0.1 | FastAPI server bind address |
| `BACKEND_PORT` | 8000 | FastAPI server port |
| `DATABASE_URL` | sqlite:///./data/devops_agent.db | Database connection string |
| `DEBUG` | False | Enable debug mode |

## Next: Phase 2 - Codebase Analysis & Detection

**After Phase 1 verification**, the next phase will implement:
- Fast codebase stack detection (language/framework identification)
- Deep analysis module (dependency parsing)
- Analysis orchestrator service

See `plan.md` for full implementation roadmap.

## Troubleshooting

**Issue**: "Session could not find repository"
- Check GitHub PAT token has `repo` scope
- Verify repository name format: `owner/repo-name`
- Ensure you have access to the repository

**Issue**: "Ollama connection failed"
- Verify Ollama is running: `ollama list`
- Check Ollama is on port 11434
- Verify gemma4 model is available: `ollama list`

**Issue**: "Database locked" errors
- Stop all running instances
- Delete `data/devops_agent.db` (it will regenerate)
- Restart the server

## Project Structure

```
DevOpsAgent/
├── backend/
│   ├── app.py                   # FastAPI main application
│   ├── requirements.txt         # Python dependencies
│   ├── config/
│   │   ├── settings.py         # Environment configuration
│   │   └── db.py               # Database setup
│   ├── models/
│   │   ├── session.py          # Session ORM model
│   │   ├── chat.py             # ChatMessage ORM model
│   │   └── ci.py               # GeneratedCI ORM model
│   ├── routes/
│   │   └── sessions.py         # Session management routes
│   ├── github/
│   │   └── manager.py          # GitHub API wrapper
│   ├── llm/
│   │   └── ollama_client.py    # Ollama LLM client
│   ├── analyzers/              # [Phase 2] Stack detection
│   ├── services/               # [Phase 3] CI generation
│   └── database/               # [Future] Migrations
├── frontend/                    # [Phase 5] React UI
├── .env.example                 # Environment template
├── plan.md                       # Full implementation plan
└── README.md                     # This file
```

---

**Current Status**: Phase 1 Complete ✅ | Ready for Phase 2 Integration
