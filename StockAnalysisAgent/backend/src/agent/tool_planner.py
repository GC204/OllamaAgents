"""Tool-planning loop that works even without native tool-calling.

Some Ollama setups/models may not emit structured tool_calls. In that case, the
LLM often prints "JSON for a function call" instead of actually calling tools.
This module implements a robust fallback planner that *decides* tool usage via
structured output, runs tools, then streams a final response.
"""

from __future__ import annotations

from typing import Any, Literal

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langchain_ollama import ChatOllama
from pydantic import BaseModel, Field

from src.agent.prompts import SYSTEM_PROMPT
from src.config import get_settings
from src.tools import AGENT_TOOLS


class NextStep(BaseModel):
    action: Literal["tool", "final"] = Field(..., description="Whether to call a tool or respond to user.")
    tool_name: str | None = Field(None, description="Tool to call when action=tool.")
    tool_args: dict[str, Any] | None = Field(None, description="Arguments for the tool when action=tool.")
    final: str | None = Field(None, description="Final answer when action=final.")


def _tools_by_name():
    return {t.name: t for t in AGENT_TOOLS}


def _format_tool_context(tool_runs: list[dict[str, Any]]) -> str:
    if not tool_runs:
        return "None"
    blocks = []
    for r in tool_runs:
        blocks.append(
            f"- Tool: {r['tool']}\n"
            f"  Args: {r.get('args', {})}\n"
            f"  Result:\n{r.get('result', '')}"
        )
    return "\n\n".join(blocks)


async def run_with_tools(messages: list[BaseMessage], max_steps: int = 6) -> tuple[list[dict[str, Any]], str | None]:
    """Runs a short plan/act loop and returns (tool_runs, optional_final_text)."""
    settings = get_settings()
    llm = ChatOllama(base_url=settings.ollama_base_url, model=settings.llm_model, temperature=0.2)
    planner = llm.with_structured_output(NextStep)
    tools = _tools_by_name()

    # last user message content is the current ask
    user_text = ""
    for m in reversed(messages):
        if isinstance(m, HumanMessage):
            user_text = m.content
            break

    tool_runs: list[dict[str, Any]] = []
    for _ in range(max_steps):
        tool_context = _format_tool_context(tool_runs)
        planning_messages: list[BaseMessage] = [
            SystemMessage(
                content=(
                    SYSTEM_PROMPT
                    + "\n\nYou are in TOOL-PLANNING mode.\n"
                    + "- Decide the next step.\n"
                    + "- If you need data (live prices/dividend yield/history/financials, sector performance, or uploaded docs), call ONE tool.\n"
                    + "- Otherwise respond with action=final.\n"
                    + "- Do NOT include any tool-call JSON in final answers.\n"
                )
            ),
            HumanMessage(
                content=(
                    f"User question:\n{user_text}\n\n"
                    f"Tool results so far:\n{tool_context}\n\n"
                    "Return the next step."
                )
            ),
        ]

        step = await planner.ainvoke(planning_messages)
        if step.action == "final":
            return tool_runs, step.final

        tool_name = (step.tool_name or "").strip()
        args = step.tool_args or {}
        tool = tools.get(tool_name)
        if tool is None:
            tool_runs.append(
                {
                    "tool": tool_name or "<missing>",
                    "args": args,
                    "result": f"Unknown tool. Available: {', '.join(sorted(tools.keys()))}",
                }
            )
            break

        try:
            # Tools created by @tool are typically sync; invoke() is fine here.
            result = tool.invoke(args)
        except Exception as e:
            result = f"Tool error: {e}"

        tool_runs.append({"tool": tool_name, "args": args, "result": result})

    return tool_runs, None


async def stream_final_answer(messages: list[BaseMessage]):
    """Stream the final answer using tool outputs as context."""
    settings = get_settings()
    llm = ChatOllama(base_url=settings.ollama_base_url, model=settings.llm_model, temperature=0.2)

    tool_runs, quick_final = await run_with_tools(messages)
    tool_context = _format_tool_context(tool_runs)

    # If the planner already produced a final string, stream it in chunks (still SSE-token friendly).
    if quick_final:
        for ch in quick_final:
            yield ch
        return

    final_messages: list[BaseMessage] = [
        SystemMessage(content=SYSTEM_PROMPT),
        SystemMessage(
            content=(
                "Use the following tool results as the factual basis for your answer.\n\n"
                f"{tool_context}\n\n"
                "If dividend yield is missing for a stock, say that you can't compute the investment needed."
            )
        ),
    ] + messages

    async for chunk in llm.astream(final_messages):
        if isinstance(chunk, AIMessage):
            if chunk.content:
                yield chunk.content
        else:
            content = getattr(chunk, "content", None)
            if content:
                yield content

