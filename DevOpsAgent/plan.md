# DevOps Agent Implementation Plan

## Overview

**Goal**: Build a web-based DevOps CI/CD agent that accepts GitHub repos, auto-detects codebase stacks, generates customized CI/CD YAML files via LLM, and creates PRs for human approval.

**Tech Stack**: 
- Backend: Python + FastAPI
- Frontend: React with TypeScript
- LLM: Gemma 4 (via Ollama on localhost:11434)
- Database: SQLite (session persistence)
- GitHub Integration: PyGithub with PAT token
- API Clients: GitHub REST API

---

## Implementation Phases

### Phase 1: Backend Foundation & GitHub Integration (Days 1-2)

**Goal**: Set up FastAPI backend with GitHub authentication, session management, and core infrastructure.

**Steps**:
1. Initialize Python project structure
   - Create folder structure: `backend/`, `frontend/`, `data/`, `config/`
   - Setup `requirements.txt` with FastAPI, PyGithub, SQLAlchemy, Ollama client, pydantic
   - Create `.env.example` for GitHub PAT, Ollama host, and ports

2. Database Layer - SQLite schema
   - Define models: `Session` (id, created_at, user_input), `ChatMessage` (session_id, role, content, timestamp), `GeneratedCI` (session_id, repo_name, branch, yaml_content, pr_url, status)
   - Use SQLAlchemy ORM for database operations
   - Create migration scripts

3. FastAPI setup
   - Create main app in `backend/app.py`
   - Setup CORS for frontend communication
   - Create routes structure (sessions, chat, github, ci_generation)

4. GitHub Integration layer
   - Class: `GitHubManager` to handle clone, repo analysis, PR creation
   - Methods: `authenticate_with_pat()`, `clone_repo()`, `create_pr()`, `get_repo_info()`
   - Store PAT token securely via environment variables

5. Session Management
   - FastAPI dependencies for session validation
   - Routes: `POST /sessions` (create), `GET /sessions/{id}` (fetch), `POST /sessions/{id}/chat` (add message)

---

### Phase 2: Codebase Analysis & Detection (Days 2-3)

**Goal**: Implement fast and deep codebase stack detection.

**Steps**:
1. Fast Detection Module (`backend/analyzers/fast_detector.py`)
   - Scan for package files: `package.json`, `requirements.txt`, `go.mod`, `pom.xml`, `Gemfile`, `Cargo.toml`, `build.gradle`, `.csproj`
   - Scan for language-specific files: `*.py`, `*.js`, `*.ts`, `*.go`, `*.java`, `*.rs`, `*.cs`
   - Return detected languages, frameworks, and primary stack

2. Deep Detection Module (`backend/analyzers/deep_detector.py`)
   - Parse package.json → extract dependencies, frameworks (React, Vue, Express, Nestjs)
   - Parse requirements.txt → extract Python packages and versions
   - Look for config files: `.github/workflows/`, `docker-compose.yml`, `Dockerfile`, `terraform/`, `k8s/`  
   - Use regex/parsing to identify architecture patterns (monorepo, microservices, etc.)
   - Return detailed stack profile with versions and architecture hints

3. Analysis Orchestrator (`backend/analyzers/analyzer.py`)
   - Class: `CodebaseAnalyzer` 
   - Method: `analyze(repo_path, deep=False)` → returns StackProfile object
   - StackProfile: {languages: [], frameworks: [], build_tools: [], testing_frameworks: [], architecture: ""}

---

### Phase 3: LLM Integration & CI Generation (Days 3-4)

**Goal**: Integrate Ollama LLM for intelligent CI/CD template generation.

**Steps**:
1. Ollama Client Setup (`backend/llm/ollama_client.py`)
   - Class: `OllamaClient`
   - Connect to `localhost:11434`
   - Method: `generate(prompt, model="gemma4")` → streams or returns generated text
   - Add error handling for connection failures

2. Prompt Engineering (`backend/llm/prompts.py`)
   - Template: `CODEBASE_ANALYZER_PROMPT` - Ask LLM to identify tech stack and suggest CI approach
   - Template: `CI_GENERATOR_PROMPT` - Generate GitHub Actions YAML based on stack + requirements
   - Include examples of good GitHub Actions workflows for validation

3. CI Generator (`backend/services/ci_generator.py`)
   - Class: `CIGenerator`
   - Method: `generate_ci(stack_profile, user_requirements, repo_details)` → returns YAML string
   - Validate generated YAML syntax
   - Add safety checks: no secrets in plain text, proper error handling sections

4. Chat-based Requirements Gathering
   - Routes in `backend/routes/chat.py`: `POST /chat/message`
   - Store user messages in DB
   - Multi-turn conversation to refine requirements:
     - Initial: "What do you want the CI to do?" (build, test, deploy, security scan, etc.)
     - Clarifications: "Found Python + React stack. Should we test both?"
     - Confirmation: "Generating CI with these settings. OK?"

---

### Phase 4: GitHub PR Creation & Approval Flow (Days 4-5)

**Goal**: Implement PR creation logic and dual approval workflows.

**Steps**:
1. PR Creation Service (`backend/services/pr_service.py`)
   - Class: `PRCreator`
   - Method: `create_branch(repo, branch_name)` → creates feature branch
   - Method: `commit_and_pr(repo, file_path, content, target_branch, title, description)` → commits and creates PR
   - Method: `get_pr_info(repo, pr_number)` → returns PR status/reviews
   - Method: `merge_pr(repo, pr_number)` or `request_review_notification(pr_number)`

2. Dual Workflow Approval
   - **Option A**: GitHub-direct approval
     - Agent creates PR in user's repo
     - Route: `GET /ci/{session_id}/approve-github` → redirects to GitHub PR URL
     - Backend polls PR status for approval/merge
   
   - **Option B**: Chat-based approval
     - Agent creates PR and shows diff in chat interface
     - Route: `POST /ci/{session_id}/approve` with diff preview
     - User confirms in chat, agent merges to target branch

3. Status Tracking
   - Routes: `GET /ci/{session_id}/status` → returns PR status, approval status
   - Database updates: Store PR URL, approval timestamp, merge status

---

### Phase 5: Frontend - Chat Interface (Days 5-6)

**Goal**: Build React chat UI with session history and approval controls.

**Steps**:
1. React Project Setup
   - Vite + React + TypeScript
   - UI Library: Tailwind CSS + shadcn/ui components
   - State management: Zustand or React Context

2. Core Pages/Components
   - `HomePage`: Initial form to input GitHub repo name and release branch
   - `ChatPage`: Chat interface with:
     - Message display area (system prompts, user inputs, LLM responses)
     - Input field for user messages
     - Real-time Ollama processing indicator
   - `ApprovalPage`: Diff preview and approval buttons
   - `SidebarSessionHistory`: List saved sessions, load past conversations

3. API Client (`frontend/src/api/client.ts`)
   - Wrapper for FastAPI endpoints
   - Handle session creation, chat messages, CI generation, approval

4. Features
   - Persist session ID in URL or localStorage
   - Real-time streaming of LLM responses (optional: WebSocket or Server-Sent Events)
   - Copy YAML to clipboard
   - Download generated YAMLs

---

### Phase 6: Integration & Testing (Days 6-7)

**Goal**: Full end-to-end integration, local testing, and deployment readiness.

**Steps**:
1. End-to-End Test Flow
   - Create test GitHub repo in your account
   - Test workflow: 
     - Input repo → Fast detect → Deep detect (if user chooses)
     - Chat: Specify CI requirements
     - Generate CI → Create PR → Review & approve
     - Verify `.github/workflows/ci.yml` appears in test repo

2. Docker Containerization (Optional but recommended)
   - `Dockerfile` for backend (Python + dependencies)
   - `docker-compose.yml` to run backend + Ollama locally
   - Simplifies deployment and dependencies

3. Configuration & Secrets Management
   - Load GitHub PAT from `.env` (use python-dotenv)
   - Support for multiple Ollama models (allow user to switch)
   - Logging setup (Python logging module)

4. Error Handling & Edge Cases
   - Handle private repos (requires proper token scopes)
   - Fallback if Ollama is down
   - Invalid YAML generation → reject and ask LLM to fix
   - Repo already has CI → warn user, allow overwrite option

---

## Relevant Files (Final Structure)

```
DevOpsAgent/
├── backend/
│   ├── app.py                          # FastAPI main app
│   ├── requirements.txt                # Python dependencies
│   ├── config/
│   │   ├── settings.py                # Environment vars, config
│   │   └── db.py                      # SQLAlchemy setup
│   ├── models/
│   │   ├── session.py                 # Session ORM model
│   │   ├── chat.py                    # ChatMessage ORM
│   │   └── ci.py                      # GeneratedCI ORM
│   ├── routes/
│   │   ├── sessions.py                # Session endpoints
│   │   ├── chat.py                    # Chat/message endpoints
│   │   └── ci.py                      # CI generation endpoints
│   ├── services/
│   │   ├── ci_generator.py            # CI generation logic
│   │   └── pr_service.py              # PR creation logic
│   ├── github/
│   │   └── manager.py                 # GitHub API wrapper
│   ├── analyzers/
│   │   ├── fast_detector.py           # Quick stack detection
│   │   ├── deep_detector.py           # Comprehensive analysis
│   │   └── analyzer.py                # Orchestrator
│   ├── llm/
│   │   ├── ollama_client.py           # Ollama connection
│   │   └── prompts.py                 # LLM prompt templates
│   └── database/
│       ├── init.py                    # DB initialization
│       └── migrations/                # Schema migrations (optional)
├── frontend/
│   ├── index.html
│   ├── package.json
│   ├── vite.config.ts
│   ├── src/
│   │   ├── App.tsx
│   │   ├── api/
│   │   │   └── client.ts              # FastAPI client wrapper
│   │   ├── pages/
│   │   │   ├── HomePage.tsx
│   │   │   ├── ChatPage.tsx
│   │   │   └── ApprovalPage.tsx
│   │   ├── components/
│   │   │   ├── ChatMessage.tsx
│   │   │   ├── SessionHistory.tsx
│   │   │   └── ApprovalDiff.tsx
│   │   ├── hooks/
│   │   │   └── useSession.ts
│   │   ├── store/
│   │   │   └── sessionStore.ts        # Zustand state
│   │   └── styles/
│   │       └── globals.css            # Tailwind setup
├── .env.example                        # Sample env vars
├── docker-compose.yml                 # Local Ollama + backend
├── Dockerfile                         # Backend container image
└── README.md                          # Setup and usage instructions
```

---

## Verification Steps

1. **Backend Setup Complete**
   - [ ] FastAPI server starts without errors: `python backend/app.py`
   - [ ] SQLite DB created with proper schema
   - [ ] GitHub authentication tested with real PAT token

2. **Analysis Module Verification**
   - [ ] Fast detection correctly identifies Python, Node, Go repos
   - [ ] Deep detection parses dependencies accurately
   - [ ] New language support is easy to add

3. **LLM Integration**
   - [ ] Ollama connection successful (test with simple prompt)
   - [ ] Generated YAMLs are valid GitHub Actions syntax (use `yamllint`)
   - [ ] No secrets/hardcoded values in generated YAML

4. **PR Flow E2E Test**
   - [ ] Create test repo in GitHub account
   - [ ] Full flow: Repo input → Chat → CI generation → PR creation → Manual approval
   - [ ] PR contains correct `.github/workflows/ci.yml` file
   - [ ] YAML executes successfully on a commit (if possible)

5. **Frontend**
   - [ ] Chat UI loads and connects to backend
   - [ ] Messages persist across page reloads (SQLite backend)
   - [ ] Approval workflow works for both options (GitHub redirect + chat approval)
   - [ ] Mobile-friendly Tailwind layout

---

## Key Decisions & Scope

**Included**:
- GitHub Actions workflows only (not GitLab, Bitbucket, etc.)
- Public and private repo support (with PAT scopes)
- Customizable CI via multi-turn chat
- Dual approval workflows (GitHub + chat)
- Basic security scanning suggestions (no pre-built integrations)

**Excluded**:
- Self-hosted runners configuration (out of scope for v1)
- Secrets management UI (handled via GitHub Settings → just advice in chat)
- Advanced deployment automation (Terraform, Helm, etc.) - mention in CI but don't generate
- Multi-user/team management (single user per session for v1)
- CI testing/validation in actual GitHub (would need workflow dispatch setup)

**Assumptions**:
- Users have valid GitHub PAT with repo write + workflow permissions
- Ollama is always running on localhost:11434
- Repos are HTTPS-cloneable (public or user has access)
- Target release branch exists in the repo

---

## Implementation Priority (If Time-Limited)

**MVP (Minimum Viable Product) - Week 1**:
- Phases 1–3 (Backend + Analysis + LLM)
- Basic chat interface in Postman or curl
- Test with real repo manually

**v0.5 Release - Week 2**:
- Phase 4 (PR creation for GitHub-direct approval only)
- Basic React chat UI (Phases 5)
- Fully working end-to-end flow

**v1.0 Release - Week 3**:
- All phases completed
- Both approval workflows
- Full production-ready setup

---

## Tech Stack Summary

| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| Backend Framework | FastAPI | Latest | REST API, async support |
| Database | SQLite + SQLAlchemy | Python 3.10+ | Session & chat persistence |
| GitHub API | PyGithub | Latest | Repo interaction, PR creation |
| LLM Client | Python requests | Latest | Ollama API calls |
| LLM Server | Ollama | Running locally | Gemma 4 model execution |
| Frontend | React + TypeScript | Latest | Web UI |
| UI Library | Tailwind CSS | Latest | Styling |
| YAML Validation | yamllint | Latest | Validate generated workflows |
| Containerization | Docker | Latest | Local deployment |

---

## Next Steps

1. **User Review** → Approve plan or request modifications
2. **Implementation Kickoff** → Start Phase 1 backend setup
3. **Weekly check-ins** → Adjust based on findings
