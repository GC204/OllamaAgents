"""Chat endpoint with streaming."""
from langchain_core.messages import HumanMessage, AIMessage
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import json

from src.agent.tool_planner import stream_final_answer

router = APIRouter()


class ChatRequest(BaseModel):
    message: str
    history: list[dict] = []


def _history_to_messages(history: list[dict]):
    messages = []
    for h in history:
        role = h.get("role")
        content = h.get("content", "")
        if role == "user":
            messages.append(HumanMessage(content=content))
        elif role == "assistant":
            messages.append(AIMessage(content=content))
    return messages


async def stream_chat(message: str, history: list[dict]):
    messages = _history_to_messages(history) + [HumanMessage(content=message)]
    try:
        # Immediately tell UI we're working (even before first token).
        yield f"data: {json.dumps({'type': 'status', 'content': 'thinking'})}\n\n"
        async for token in stream_final_answer(messages):
            if token:
                yield f"data: {json.dumps({'type': 'token', 'content': token})}\n\n"
        yield f"data: {json.dumps({'type': 'done'})}\n\n"
    except Exception as e:
        yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"


@router.post("/chat")
async def chat(request: ChatRequest):
    return StreamingResponse(
        stream_chat(request.message, request.history),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
