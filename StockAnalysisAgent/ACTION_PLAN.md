# Action Plan: RAG-Based Stock Advisor Agent

Build a **Financial Stock Advisor AI** using LangGraph (ReAct agent), LangChain tools, sentence-transformers for RAG, and a Vite frontend—all backed by local Ollama.

---

## 1. High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         Vite Frontend (React/TS)                         │
│  Chat UI | File upload | Charts/tables | Streaming responses             │
└─────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                      Backend API (FastAPI / Node)                        │
│  /chat (stream) | /ingest | /health | CORS, auth (optional)              │
└─────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    LangGraph ReAct Agent (Python)                        │
│  StateGraph: tools → conditional → LLM (Ollama) → loop until finish      │
└─────────────────────────────────────────────────────────────────────────┘
         │                    │                    │
         ▼                    ▼                    ▼
┌──────────────┐    ┌─────────────────┐    ┌──────────────────┐
│ RAG Retriever│    │ LangChain Tools │    │ Document Loaders  │
│ (sentence-   │    │ market, sector, │    │ PDF/DOCX/XLSX/    │
│  transformers│    │ company, eval   │    │ CSV, images       │
│ + vector DB) │    │ file_analysis   │    │                   │
└──────────────┘    └─────────────────┘    └──────────────────┘
         │                    │                    │
         └────────────────────┴────────────────────┘
                                      │
                                      ▼
                            ┌─────────────────┐
                            │ Ollama (local)  │
                            │ llama3 / mistral│
                            └─────────────────┘
```

---

## 2. Phase-by-Phase Action Plan

### Phase 1: Project Setup & Structure

| Step | Task | Details |
|------|------|---------|
| 1.1 | Repo structure | `backend/` (Python: agent + RAG + API), `frontend/` (Vite + React + TS), `data/` or `documents/` for ingested files |
| 1.2 | Python env | `pyproject.toml` or `requirements.txt`: `langgraph`, `langchain`, `langchain-community`, `sentence-transformers`, `chromadb` (or `faiss`), doc loaders (`pypdf`, `python-docx`, `openpyxl`, `pandas`), `fastapi`, `uvicorn`, `ollama` / `langchain-ollama` |
| 1.3 | Node/Vite | `npm create vite@latest frontend -- --template react-ts`; add Tailwind (optional), fetch/streaming for chat |
| 1.4 | Config | `.env` for `OLLAMA_BASE_URL`, `EMBED_MODEL`, `LLM_MODEL`, vector store path; config module in backend |

**Deliverable:** Monorepo with backend (Python) and frontend (Vite) running locally.

---

### Phase 2: RAG Pipeline (Embeddings + Vector Store)

| Step | Task | Details |
|------|------|---------|
| 2.1 | Embeddings | Use **sentence-transformers** (e.g. `all-MiniLM-L6-v2` or `all-mpnet-base-v2`) via LangChain `HuggingFaceEmbeddings`; run locally, no API key |
| 2.2 | Vector store | **ChromaDB** or **FAISS**; persist under `data/vector_store` or similar |
| 2.3 | Chunking | LangChain `RecursiveCharacterTextSplitter` (e.g. 512–1024 chars, overlap 128); for tables consider `MarkdownHeaderTextSplitter` or table-aware splitting if needed |
| 2.4 | Retriever | Top-k retrieval (e.g. k=5–10); optionally add metadata filter by source type (market report, sector, company, user file) |
| 2.5 | RAG chain (optional) | Simple “retrieve → format context → pass to LLM” for non-agent queries; or expose only retriever for the agent to call via a tool |

**Deliverable:** Script or API to ingest text/documents into the vector store and a retriever that returns relevant chunks for a query.

---

### Phase 3: Document Ingestion (Files & Parsing)

| Step | Task | Details |
|------|------|---------|
| 3.1 | Loaders | LangChain document loaders: `PyPDFLoader`, `Docx2txtLoader` (or `UnstructuredWordDocumentLoader`), `UnstructuredExcelLoader` / pandas + `CSVLoader`, and for images use `UnstructuredImageLoader` or vision model (e.g. Ollama vision) for table extraction |
| 3.2 | Parsing pipeline | Per file type: load → extract text/tables → normalize (e.g. tables to markdown or structured rows) → chunk → embed → add to vector store; store metadata (filename, type, upload time) |
| 3.3 | API endpoint | `POST /ingest`: accept multipart file(s); run parsing pipeline; return success/failure and doc IDs |
| 3.4 | Optional: table extraction from images | Use Ollama vision (e.g. `llava`) to describe table or extract structure, then feed into RAG or structured output |

**Deliverable:** Backend can accept PDF, DOCX, XLSX, CSV, and optionally images; all content searchable via RAG.

---

### Phase 4: LangChain Tools for the Agent

| Step | Task | Details |
|------|------|---------|
| 4.1 | RAG tool | One or more tools: “search_financial_docs(query)”, “search_market_trends(query)” that call the retriever and return formatted context (snippets + source). |
| 4.2 | Market / sector tools | Tools that wrap external APIs or local data (e.g. “get_market_trends()”, “get_sector_performance(sector_ids?)”, “compare_sectors(sector_a, sector_b)”). If no API, use RAG over ingested market/sector reports. |
| 4.3 | Company / stock tools | “get_company_financials(symbol)”, “get_technical_indicators(symbol)”—implement via API or RAG over ingested docs. |
| 4.4 | File analysis tool | “analyze_uploaded_document(doc_id or path)” that runs extraction + optional summarization using the same loaders and LLM. |
| 4.5 | Tool descriptions | Clear, concise descriptions so the ReAct agent can choose when to call each tool (e.g. “Use when the user asks for sector comparison”). |

**Deliverable:** A set of LangChain tools (functions + `@tool` or `StructuredTool`) that the agent can invoke.

---

### Phase 5: LangGraph ReAct Agent

| Step | Task | Details |
|------|------|---------|
| 5.1 | State schema | Define state (e.g. `messages`, `current_tool_calls`, `intermediate_steps`, `context`); use LangGraph’s `MessagesState` or custom TypedDict. |
| 5.2 | Graph nodes | **Agent node:** call Ollama (via `ChatOllama`) with system prompt (ideation guidelines) and prompt that asks for ReAct-style reasoning and tool calls; **Tools node:** execute selected tools and append results to state. |
| 5.3 | Edges | Agent → conditional edge: if tool_calls → tools node; else → end. Tools node → back to agent (loop until no more tool calls). |
| 5.4 | Ollama integration | Use `langchain-ollama` `ChatOllama` with `base_url` from config; ensure model supports tool/function calling (e.g. `llama3.1`, `mistral`, `qwen2.5`) or use ReAct parsing from text. |
| 5.5 | System prompt | Embed ideation.txt: role (financial advisor), capabilities (market, sector, company, file analysis), guidelines (ground in data, structured output, no speculation). |
| 5.6 | Streaming | Expose token stream from the final agent response (and optionally from tool outputs) so the UI can show progressive output. |

**Deliverable:** A LangGraph ReAct agent that uses Ollama and the defined tools; invokable from Python with streaming.

---

### Phase 6: Backend API

| Step | Task | Details |
|------|------|---------|
| 6.1 | Framework | FastAPI app: CORS for Vite dev server, optional rate limiting and request size limits. |
| 6.2 | Endpoints | `POST /chat`: body `{ "message": "...", "history": [...] }`; stream SSE or WebSocket; `POST /ingest`: multipart file upload; `GET /health`: Ollama + vector store liveness. |
| 6.3 | Agent invocation | In `/chat`, build message list from history + new message, run LangGraph agent stream, yield chunks. |
| 6.4 | Error handling | Timeouts for Ollama, clear errors for missing model or failed ingestion. |

**Deliverable:** Backend that accepts chat and file uploads and streams agent responses.

---

### Phase 7: Vite Frontend (UI)

| Step | Task | Details |
|------|------|---------|
| 7.1 | Chat interface | Single-page chat: input box, send button, message list (user/assistant); support streaming (fetch with ReadableStream or EventSource). |
| 7.2 | File upload | Drag-and-drop or file picker for PDF/DOCX/XLSX/CSV/images; show upload progress and call `POST /ingest`; optionally attach “context” to next message (e.g. “Analyze the file I just uploaded”). |
| 7.3 | Structured display | Where the assistant returns markdown tables or bullet points, render with a markdown component; optional simple charts (e.g. Chart.js or Recharts) if you add structured data in responses (e.g. sector comparison). |
| 7.4 | UX | Loading states during tool use and streaming; clear errors; optional dark/light theme. |

**Deliverable:** Vite app that talks to the backend for chat (streaming) and file ingestion, with a clean, usable UI.

---

### Phase 8: Integration, Testing & Polish

| Step | Task | Details |
|------|------|---------|
| 8.1 | End-to-end | Run Ollama with a chosen model; ingest a sample PDF/Excel; ask “Compare IT and Pharma” and “Analyze this file”; verify RAG and tools are called and response is grounded. |
| 8.2 | Sentence-transformers | Confirm embedding model loads and runs on your OS (Windows); use a small model if memory is a concern. |
| 8.3 | Docs & runbooks | README: how to install backend deps, run Ollama, start backend and frontend; optional Docker Compose for backend + ChromaDB. |

**Deliverable:** Working end-to-end flow, README, and basic run instructions.

---

## 3. Suggested Tech Stack Summary

| Layer | Choice | Notes |
|-------|--------|-------|
| Agent / orchestration | **LangGraph** | ReAct loop with tools and Ollama |
| LLM | **Ollama** (local) | Via `langchain-ollama` `ChatOllama` |
| Embeddings | **sentence-transformers** | Via LangChain `HuggingFaceEmbeddings` |
| Vector store | **ChromaDB** or **FAISS** | Persistent, local |
| Tools | **LangChain tools** | RAG, market/sector/company, file analysis |
| Document loaders | **LangChain** | PyPDF, Docx2txt, UnstructuredExcel, CSV, image |
| Backend | **FastAPI** | Async, SSE streaming, file upload |
| Frontend | **Vite + React + TypeScript** | Chat UI, file upload, streaming |

---

## 4. File Structure (Suggested)

```
StockAnalysisAgent/
├── backend/
│   ├── pyproject.toml or requirements.txt
│   ├── .env.example
│   ├── src/
│   │   ├── config.py
│   │   ├── rag/
│   │   │   ├── embeddings.py    # sentence-transformers + LangChain
│   │   │   ├── vector_store.py # Chroma/FAISS init and persist
│   │   │   ├── retriever.py
│   │   │   └── chunking.py
│   │   ├── ingestion/
│   │   │   ├── loaders.py      # PDF, DOCX, XLSX, CSV, image
│   │   │   └── pipeline.py     # load → chunk → embed → store
│   │   ├── tools/
│   │   │   ├── rag_tools.py
│   │   │   ├── market_sector_tools.py
│   │   │   └── file_analysis_tool.py
│   │   ├── agent/
│   │   │   ├── state.py
│   │   │   ├── graph.py        # LangGraph ReAct definition
│   │   │   └── prompts.py
│   │   └── api/
│   │       ├── main.py         # FastAPI app
│   │       └── routes/
│   │           ├── chat.py
│   │           └── ingest.py
│   └── data/                   # vector store persist, uploaded files
├── frontend/
│   ├── package.json
│   ├── vite.config.ts
│   ├── index.html
│   └── src/
│       ├── App.tsx
│       ├── components/
│       │   ├── Chat.tsx
│       │   ├── MessageList.tsx
│       │   ├── FileUpload.tsx
│       │   └── MarkdownRenderer.tsx
│       └── api/
│           └── client.ts       # fetch / stream to backend
├── ideation.txt
└── ACTION_PLAN.md (this file)
```

---

## 5. Implementation Order (Checklist)

1. [ ] Phase 1: Project setup (backend + frontend skeletons, env)
2. [ ] Phase 2: RAG pipeline (embeddings, vector store, retriever)
3. [ ] Phase 3: Document ingestion (loaders + `/ingest`)
4. [ ] Phase 4: LangChain tools (RAG, market/sector/company, file analysis)
5. [ ] Phase 5: LangGraph ReAct agent (state, graph, Ollama, streaming)
6. [ ] Phase 6: Backend API (`/chat` stream, `/ingest`, `/health`)
7. [ ] Phase 7: Vite UI (chat, upload, markdown, optional charts)
8. [ ] Phase 8: E2E test and README

---

## 6. Notes

- **Ollama tool calling:** Prefer a model that supports native tool/function calls (e.g. `llama3.1`, `mistral`) so LangChain can bind tools to the LLM; otherwise implement a ReAct parser that extracts tool name and arguments from the model’s text output.
- **Sentence-transformers on Windows:** Use a small model first (e.g. `all-MiniLM-L6-v2`) to avoid long first-time download and memory issues.
- **Data source:** For “market trends” and “sector performance” you can start with RAG over ingested reports; later add live APIs (e.g. Yahoo Finance, Alpha Vantage) as additional tools.

You can use this plan as a single reference and implement phase by phase, or slice vertically (e.g. minimal RAG + one tool + agent + simple UI) for an early end-to-end demo.
