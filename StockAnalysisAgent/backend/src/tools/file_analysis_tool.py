"""Tool to analyze an uploaded file by re-retrieving its content and summarizing."""
from langchain_core.tools import tool

from src.rag import get_retriever


@tool
def analyze_uploaded_document(query: str) -> str:
    """Analyze content from user-uploaded documents. Pass a natural-language query describing what to analyze (e.g. 'revenue growth and P/E ratio', 'summarize financials', 'compare quarters').
    Use when the user refers to a file they uploaded or asks to analyze document content."""
    retriever = get_retriever()
    docs = retriever.invoke(query)
    if not docs:
        return "No document content found. Ensure the user has uploaded a file (PDF, DOCX, XLSX, CSV) and try a more general query."
    parts = [d.page_content for d in docs]
    return "\n\n".join(parts)
