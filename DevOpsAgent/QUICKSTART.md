# Quick Start Guide - DevOps CI/CD Agent

## 🚀 Get Running in 5 Minutes

### Prerequisites
- Python 3.10+
- Node.js 16+
- GitHub PAT token (with `repo` and `workflow` scopes)
- Ollama running locally with Gemma 4 model

---

## Step 1: Setup Environment

### 1.1 Clone the Project
```bash
cd e:\Ollama\Agents\DevOpsAgent
```

### 1.2 Create `.env` File
```bash
# Copy the example
copy .env.example .env

# Edit .env with your values
# IMPORTANT: Set GITHUB_PAT_TOKEN to your GitHub personal access token
```

**Required `.env` values:**
```
GITHUB_PAT_TOKEN=ghp_your_token_here
OLLAMA_HOST=localhost
OLLAMA_PORT=11434
OLLAMA_MODEL=gemma4
BACKEND_PORT=8000
```

### 1.3 Ensure Ollama is Running
```bash
# In a new terminal, start Ollama if not already running
ollama serve

# In another terminal, verify Gemma 4 is installed
ollama list

# If not present, pull it
ollama pull gemma4
```

---

## Step 2: Start Backend

```bash
# Terminal 1: Backend
cd backend
python -m venv venv
venv\Scripts\activate  # Windows

pip install -r requirements.txt

python -m uvicorn app:app --reload --port 8000
```

**Expected output:**
```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete
```

---

## Step 3: Start Frontend (Optional)

```bash
# Terminal 2: Frontend
cd frontend
npm install
npm run dev
```

**Expected output:**
```
  ➜  Local:   http://localhost:5173/
  ➜  press h to show help
```

---

## Step 4: Test the System

### Option A: Using the Web UI (Recommended)
1. Go to http://localhost:5173
2. Enter a GitHub repo: `owner/repo-name`
3. Enter release branch (default: `main`)
4. Click "Create Session"
5. Chat with the AI about your CI requirements

### Option B: Using Terminal Commands

#### Create a Session
```bash
curl -X POST http://localhost:8000/api/sessions \
  -H "Content-Type: application/json" \
  -d '{
    "repo_name": "owner/repo-name",
    "release_branch": "main"
  }'
```

Save the returned `id` for next steps.

#### Analyze the Repository
```bash
curl -X POST http://localhost:8000/api/sessions/{SESSION_ID}/quick-analyze
```

This will:
- Clone the repo
- Detect languages, frameworks, build tools
- Return stack analysis

#### Chat About CI Requirements
```bash
curl -X POST http://localhost:8000/api/sessions/{SESSION_ID}/ai-response \
  -H "Content-Type: application/json" \
  -d '{
    "content": "I need to test on Python 3.9 and 3.10 with pytest and coverage reporting"
  }'
```

#### Generate CI Workflow
```bash
curl -X POST http://localhost:8000/api/sessions/{SESSION_ID}/generate-ci \
  -H "Content-Type: application/json" \
  -d '{
    "requirements": "Python project with pytest, coverage, and GitHub Actions deployment"
  }'
```

Save the returned `id` (it's the CI ID).

#### Create Pull Request
```bash
curl -X POST http://localhost:8000/api/sessions/{SESSION_ID}/ci/{CI_ID}/create-pr
```

This creates a `.github/workflows/ci.yml` PR on your repo.

#### View PR Changes
```bash
curl http://localhost:8000/api/sessions/{SESSION_ID}/ci/{CI_ID}/pr-diff
```

#### Approve & Merge PR
```bash
curl -X POST http://localhost:8000/api/sessions/{SESSION_ID}/ci/{CI_ID}/approve-github \
  -H "Content-Type: application/json" \
  -d '{"merge_method": "squash"}'
```

---

## Architecture Overview

```
User Browser (http://localhost:5173)
        ↓
React Frontend (HomePage → ChatPage → ApprovalPage)
        ↓
FastAPI Backend (http://localhost:8000/api)
        ↓
┌─────────────────────────────┐
│   Codebase Analyzer         │
│   - Fast Detection          │
│   - Deep Analysis           │
└─────────────────────────────┘
        ↓
┌─────────────────────────────┐
│   Ollama LLM                │
│   - Chat Responses          │
│   - CI Generation           │
└─────────────────────────────┘
        ↓
┌─────────────────────────────┐
│   GitHub Integration        │
│   - Repository Cloning      │
│   - PR Creation             │
│   - Workflow Merge          │
└─────────────────────────────┘
        ↓
SQLite Database (Session + Chat History)
```

---

## API Endpoints Cheat Sheet

### Sessions
| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/api/sessions` | Create session |
| GET | `/api/sessions/{id}` | Get session |
| LIST | `/api/sessions` | List sessions |
| DELETE | `/api/sessions/{id}` | End session |

### Analysis
| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/api/sessions/{id}/quick-analyze` | Fast detection |
| POST | `/api/sessions/{id}/analyze` | Deep analysis |

### Chat & Generation
| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/api/sessions/{id}/ai-response` | Chat message |
| GET | `/api/sessions/{id}/chat` | Get history |
| POST | `/api/sessions/{id}/generate-ci` | Generate YAML |

### CI/PR Management
| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/api/sessions/{id}/ci/{ci_id}/create-pr` | Create PR |
| GET | `/api/sessions/{id}/ci/{ci_id}/pr-status` | PR status |
| GET | `/api/sessions/{id}/ci/{ci_id}/pr-diff` | View changes |
| POST | `/api/sessions/{id}/ci/{ci_id}/approve-github` | Merge PR |
| POST | `/api/sessions/{id}/ci/{ci_id}/approve-chat` | Chat approval |

---

## Troubleshooting

### Backend Won't Start
```bash
# Check Python version
python --version  # Should be 3.10+

# Check dependencies
pip install -r requirements.txt --upgrade

# Check port 8000 is free
netstat -ano | findstr :8000
```

### "Repository not found" Error
- Verify format: `owner/repo` (case-sensitive)
- Check GitHub PAT has repo access
- Run: `curl -H "Authorization: token YOUR_PAT" https://api.github.com/user`

### "Ollama connection failed"
```bash
# Check Ollama status
curl http://localhost:11434/api/tags

# Verify model is installed
ollama list | findstr gemma

# If not found, install it
ollama pull gemma4
```

### Frontend API Errors
- Check backend is running: `curl http://localhost:8000/health`
- Clear browser cache: Ctrl+Shift+Delete
- Check browser console: F12 → Console tab

### Database Errors
```bash
# Reset database
rm backend\data\devops_agent.db

# Restart backend to recreate
python -m uvicorn app:app --reload
```

---

## Project Structure Quick Reference

```
backend/
  ├── app.py                 ← Main FastAPI app
  ├── requirements.txt       ← Dependencies
  ├── config/                ← Settings & database
  ├── models/                ← SQLAlchemy models
  ├── routes/                ← API endpoints
  ├── services/              ← Business logic
  ├── github/                ← GitHub wrapper
  ├── analyzers/             ← Stack detection
  └── llm/                   ← Ollama client

frontend/
  ├── package.json           ← Dependencies
  ├── vite.config.ts         ← Dev server config
  ├── src/
  │   ├── App.tsx            ← Main router
  │   ├── pages/             ← Pages (HomePage, ChatPage, etc)
  │   ├── components/        ← Reusable components
  │   ├── api/               ← API client
  │   └── store/             ← State management
```

---

## Common Workflows

### Scenario 1: User Workflow (Homepage)
1. Enter `owner/repo` and release branch
2. Click "Create Session"
3. View repository analysis
4. Chat with AI about CI requirements
5. Generate workflow
6. Review and approve PR

### Scenario 2: Testing Multiple Languages
1. Create session with Java repo
2. AI detects Maven + JUnit
3. Request: "Setup CI for Java with Maven builds and JUnit tests"
4. AI generates Maven workflow
5. Request: "Add SonarQube quality gates"
6. Updates YAML with SonarQube integration
7. Generate and merge PR

### Scenario 3: Experienced DevOps Engineer
1. Create session
2. Skip to CI generation immediately
3. Provide detailed requirements including container registry, secrets, etc.
4. Review generated YAML
5. Request specific improvements
6. Finalize and merge

---

## Performance Notes

- **Analysis Speed**: Fast detection: <1s, Deep analysis: 5-15s (depends on repo size)
- **LLM Generation**: 10-30s (depends on Ollama model size and system)
- **PR Creation**: 2-5s (GitHub API calls)
- **Database**: All queries optimized with proper indexes

---

## Next Steps After Quickstart

1. **Complete Frontend Pages**
   - Implement `ChatPage.tsx` for multi-turn chat
   - Implement `ApprovalPage.tsx` for PR review
   - Add route integration

2. **Real Testing**
   - Test with your actual private/public GitHub repos
   - Verify workflows execute correctly in GitHub Actions
   - Collect feedback on generated YAML quality

3. **Deployment** (if ready)
   - Docker containerization
   - Azure App Service deployment
   - CI/CD pipeline for the agent itself

4. **Enhancement**
   - Add template library
   - Support more CI/CD platforms
   - Advanced security scanning

---

## Support Resources

- **Backend Docs**: See `IMPLEMENTATION_SUMMARY.md`
- **API Documentation**: Visit `http://localhost:8000/docs` (Swagger UI)
- **Alt API Docs**: Visit `http://localhost:8000/redoc` (ReDoc)
- **GitHub API Help**: https://docs.github.com/en/rest
- **Ollama Docs**: https://github.com/ollama/ollama

---

## Emergency Commands

```bash
# Hard reset everything
rm -r backend/venv
rm backend/data/*.db
exit python processes

# Restart from scratch
venv\Scripts\activate
pip install -r requirements.txt
python -m uvicorn app:app --reload

# Kill process on port 8000 (Windows)
taskkill /F /PID (Get-Process -Name python | where {$_.Port -eq 8000})

# Kill process on port 5173 (Node)
taskkill /F /PID (Get-Process -Name node | where {$_.Port -eq 5173})
```

---

**You're all set! 🎉**

Start the backend and frontend, then open http://localhost:5173 to begin!

Questions? Check IMPLEMENTATION_SUMMARY.md or see `/api/docs` for full API documentation.
