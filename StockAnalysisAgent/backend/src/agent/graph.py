"""LangGraph ReAct agent with Ollama and tools."""
from langchain_ollama import ChatOllama
from langgraph.prebuilt import create_react_agent

from src.config import get_settings
from src.agent.prompts import SYSTEM_PROMPT
from src.tools import AGENT_TOOLS


def get_agent():
    settings = get_settings()
    llm = ChatOllama(
        base_url=settings.ollama_base_url,
        model=settings.llm_model,
        temperature=0.2,
    )
    return create_react_agent(llm, AGENT_TOOLS, prompt=SYSTEM_PROMPT)
