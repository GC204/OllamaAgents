"""RAG tools for the agent: search financial documents."""
from langchain_core.tools import tool

from src.rag import get_retriever


@tool
def search_financial_docs(query: str) -> str:
    """Search ingested financial documents, reports, and uploaded files for relevant data.
    Use this when the user asks about market trends, sector performance, company financials,
    or any analysis that should be grounded in uploaded or ingested documents."""
    retriever = get_retriever()
    docs = retriever.invoke(query)
    if not docs:
        return "No relevant documents found for this query. Consider asking the user to upload relevant reports or data."
    parts = []
    for i, d in enumerate(docs, 1):
        source = d.metadata.get("filename", d.metadata.get("source", "unknown"))
        parts.append(f"[Source {i}: {source}]\n{d.page_content}")
    return "\n\n---\n\n".join(parts)
