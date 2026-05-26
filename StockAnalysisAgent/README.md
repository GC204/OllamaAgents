# Stock Advisor Agent

RAG-based financial stock advisor: LangGraph ReAct agent + sentence-transformers + Ollama + Vite UI.

## Prerequisites

- **Python 3.11+**
- **Node.js 18+**
- **Ollama** with `llama3.1` (or set `LLM_MODEL` in backend `.env`)

## Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate   # Windows
# source .venv/bin/activate  # macOS/Linux
pip install -r requirements.txt
copy .env.example .env   # Windows — edit if needed
python run.py
```

API: `http://localhost:8000`  
Endpoints: `POST /api/chat` (stream), `POST /api/ingest`, `GET /api/health`

## Frontend

```bash
cd frontend
npm install
npm run dev
```

UI: `http://localhost:5173`  
Vite proxies `/api` to the backend.

## Usage

1. Start Ollama and pull the model: `ollama pull llama3.1`
2. Start backend, then frontend.
3. Optionally **upload** a PDF/DOCX/XLSX/CSV — it is ingested into the RAG store.
4. **Chat**: e.g. “What are the top profit-making sectors?”, “Compare IT and Pharma”, “Summarize the financials from the file I uploaded.”

## Project layout

- `backend/` — FastAPI, LangGraph ReAct agent, RAG (ChromaDB + sentence-transformers), ingestion, tools
- `frontend/` — Vite + React + TypeScript, chat UI with streaming and file upload
- `ideation.txt` — Agent role and capabilities
- `ACTION_PLAN.md` — Build plan
