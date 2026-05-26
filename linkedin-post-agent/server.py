"""FastAPI server for LinkedIn Post Generator web UI."""

import asyncio
import json
from pathlib import Path
from typing import Optional, List
from datetime import datetime

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from config import DRAFTS_DIR, DATA_DIR
from trends import trend_fetcher
from generator import post_generator
from linkedin import linkedin_browser
from llm import llm_client
from rag import rag_search

app = FastAPI(title="LinkedIn Post Generator", version="1.0.0")

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
STATIC_DIR = Path(__file__).parent / "static"
STATIC_DIR.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


# ============== Pydantic Models ==============

class TrendRequest(BaseModel):
    limit: int = 15


class GenerateRequest(BaseModel):
    topic: str
    trend_context: Optional[str] = None
    angle: Optional[str] = None
    use_rag: bool = True


class RAGSearchRequest(BaseModel):
    query: str
    num_results: int = 5


class RefineRequest(BaseModel):
    draft_id: str
    instruction: str


class StyleAnalysisRequest(BaseModel):
    sample_posts: List[str]


class PostRequest(BaseModel):
    draft_id: str


class DraftEditRequest(BaseModel):
    draft_id: str
    content: str


# ============== API Routes ==============

@app.get("/")
async def root():
    """Serve the main UI."""
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    ollama_ok = llm_client._check_connection()
    return {
        "status": "healthy" if ollama_ok else "degraded",
        "ollama_connected": ollama_ok,
        "timestamp": datetime.now().isoformat(),
    }


@app.get("/api/trends")
async def get_trends(limit: int = 15):
    """Fetch trending topics."""
    try:
        trends = trend_fetcher.get_trending_topics(limit=limit)
        return {"success": True, "trends": trends, "count": len(trends)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/generate")
async def generate_post(request: GenerateRequest):
    """Generate a new post draft with optional RAG context."""
    try:
        post = post_generator.generate_post(
            topic=request.topic,
            trend_context=request.trend_context,
            angle=request.angle,
            use_rag=request.use_rag,
        )
        draft_path = post_generator.save_draft(post, request.topic)

        return {
            "success": True,
            "content": post,
            "draft_id": Path(draft_path).stem,
            "character_count": len(post),
        }
    except ConnectionError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/refine")
async def refine_draft(request: RefineRequest):
    """Refine an existing draft based on user instructions."""
    try:
        # Load the draft
        draft_file = DRAFTS_DIR / f"{request.draft_id}.json"
        if not draft_file.exists():
            raise HTTPException(status_code=404, detail="Draft not found")

        with open(draft_file, "r", encoding="utf-8") as f:
            draft = json.load(f)

        original_content = draft["content"]
        topic = draft["topic"]

        # Generate refinement using LLM
        system_prompt = """You are a writing assistant helping refine LinkedIn posts.
        Make the requested changes while maintaining the original voice and style.
        Output only the revised post content, no explanations."""

        prompt = f"""Here is a LinkedIn post draft:

---
{original_content}
---

Please refine it with this instruction: {request.instruction}

Maintain the core message but apply the requested changes.
Output only the revised post, nothing else."""

        refined_content = llm_client.generate(prompt, system=system_prompt)
        refined_content = refined_content.strip().replace("```", "").strip()

        # Update the draft
        draft["content"] = refined_content
        draft["character_count"] = len(refined_content)
        draft["refinement_history"] = draft.get("refinement_history", [])
        draft["refinement_history"].append({
            "instruction": request.instruction,
            "timestamp": datetime.now().isoformat(),
        })

        with open(draft_file, "w", encoding="utf-8") as f:
            json.dump(draft, f, indent=2)

        return {
            "success": True,
            "content": refined_content,
            "character_count": len(refined_content),
        }

    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Draft not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/drafts")
async def get_drafts():
    """Get all drafts."""
    try:
        drafts = []
        for draft_file in DRAFTS_DIR.glob("draft_*.json"):
            with open(draft_file, "r", encoding="utf-8") as f:
                draft = json.load(f)
                draft["draft_id"] = draft_file.stem
                drafts.append(draft)

        drafts.sort(key=lambda d: d.get("created_at", ""), reverse=True)
        return {"success": True, "drafts": drafts}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/drafts/{draft_id}")
async def get_draft(draft_id: str):
    """Get a specific draft."""
    draft_file = DRAFTS_DIR / f"{draft_id}.json"
    if not draft_file.exists():
        raise HTTPException(status_code=404, detail="Draft not found")

    try:
        with open(draft_file, "r", encoding="utf-8") as f:
            draft = json.load(f)
        draft["draft_id"] = draft_id
        return {"success": True, "draft": draft}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/api/drafts/{draft_id}")
async def update_draft(draft_id: str, request: DraftEditRequest):
    """Manually edit a draft."""
    draft_file = DRAFTS_DIR / f"{draft_id}.json"
    if not draft_file.exists():
        raise HTTPException(status_code=404, detail="Draft not found")

    try:
        with open(draft_file, "r", encoding="utf-8") as f:
            draft = json.load(f)

        draft["content"] = request.content
        draft["character_count"] = len(request.content)
        draft["manually_edited"] = True
        draft["edited_at"] = datetime.now().isoformat()

        with open(draft_file, "w", encoding="utf-8") as f:
            json.dump(draft, f, indent=2)

        return {"success": True, "message": "Draft updated"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/drafts/{draft_id}")
async def delete_draft(draft_id: str):
    """Delete a draft."""
    draft_file = DRAFTS_DIR / f"{draft_id}.json"
    if not draft_file.exists():
        raise HTTPException(status_code=404, detail="Draft not found")

    try:
        draft_file.unlink()
        return {"success": True, "message": "Draft deleted"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/drafts/{draft_id}/review")
async def mark_reviewed(draft_id: str):
    """Mark a draft as reviewed."""
    draft_file = DRAFTS_DIR / f"{draft_id}.json"
    if not draft_file.exists():
        raise HTTPException(status_code=404, detail="Draft not found")

    try:
        post_generator.mark_as_reviewed(str(draft_file))
        return {"success": True, "message": "Draft marked as reviewed"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/post/{draft_id}")
async def post_to_linkedin(draft_id: str):
    """Post a draft to LinkedIn."""
    draft_file = DRAFTS_DIR / f"{draft_id}.json"
    if not draft_file.exists():
        raise HTTPException(status_code=404, detail="Draft not found")

    try:
        with open(draft_file, "r", encoding="utf-8") as f:
            draft = json.load(f)

        # Initialize browser and post
        await linkedin_browser.initialize(headless=False)
        success, result = await linkedin_browser.create_post(draft["content"])
        await linkedin_browser.close()

        if success:
            post_generator.mark_as_posted(str(draft_file), result)
            return {"success": True, "post_url": result}
        else:
            raise HTTPException(status_code=500, detail=result)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/analyze-style")
async def analyze_style(request: StyleAnalysisRequest):
    """Analyze writing style from sample posts."""
    try:
        profile = post_generator.analyze_writing_style(request.sample_posts)
        return {"success": True, "profile": profile}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/style-profile")
async def get_style_profile():
    """Get the current style profile."""
    try:
        profile = post_generator.style_profile
        return {"success": True, "profile": profile}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/models")
async def get_available_models():
    """Get available Ollama models."""
    try:
        models = llm_client.get_available_models()
        return {"success": True, "models": models}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/rag/search")
async def rag_search_endpoint(request: RAGSearchRequest):
    """Search web for context using RAG."""
    try:
        results = rag_search.search_web(request.query, num_results=request.num_results)
        return {
            "success": True,
            "results": [
                {
                    "title": r.title,
                    "url": r.url,
                    "summary": r.summary,
                    "source": r.source,
                    "published_date": r.published_date,
                }
                for r in results
            ],
            "count": len(results),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/rag/trending-tech")
async def get_trending_tech():
    """Get trending tech topics from web search."""
    try:
        results = rag_search.search_trending_tech()
        return {
            "success": True,
            "trends": [
                {
                    "title": r.title,
                    "url": r.url,
                    "summary": r.summary,
                    "source": r.source,
                }
                for r in results
            ],
            "count": len(results),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/rag/context")
async def get_rag_context(request: RAGSearchRequest):
    """Get RAG context for a specific topic."""
    try:
        context = rag_search.get_context_for_topic(request.query, max_results=request.num_results)
        return {
            "success": True,
            "context": context,
            "topic": request.query,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============== HTML Route ==============

@app.get("/app", response_class=HTMLResponse)
async def serve_ui():
    """Serve the main application UI."""
    return FileResponse(STATIC_DIR / "index.html")
