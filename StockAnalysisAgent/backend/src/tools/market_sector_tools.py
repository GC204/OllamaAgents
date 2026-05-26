"""Market and sector tools. RAG-based when no external API is configured."""
from langchain_core.tools import tool

from src.rag import get_retriever


@tool
def get_market_trends() -> str:
    """Get current market trends: bullish/bearish signals, sector rotation, macroeconomic indicators.
    Use when the user asks about overall market trends, top sectors, or profit/loss making sectors."""
    retriever = get_retriever()
    docs = retriever.invoke("market trends sector performance bullish bearish macroeconomic indicators")
    if not docs:
        return (
            "No market trend data found in ingested documents. "
            "Ask the user to upload market reports or sector summaries, or use search_financial_docs with a specific query."
        )
    parts = [d.page_content for d in docs]
    return "\n\n".join(parts)


@tool
def compare_sectors(sector_a: str, sector_b: str) -> str:
    """Compare performance of two sectors (e.g. IT vs Pharma, Banking vs FMCG).
    Use when the user wants to compare two industries or sectors."""
    retriever = get_retriever()
    query = f"sector comparison {sector_a} {sector_b} performance growth"
    docs = retriever.invoke(query)
    if not docs:
        return (
            f"No comparative data found for {sector_a} vs {sector_b}. "
            "Try search_financial_docs with the sector names or ask the user to upload relevant reports."
        )
    parts = [d.page_content for d in docs]
    return "\n\n".join(parts)


@tool
def get_company_financials(company_or_symbol: str) -> str:
    """Get financial data for a company: balance sheet, income statement, cash flow, P/E, EPS.
    Use when the user asks about a specific company's financials or stock fundamentals."""
    retriever = get_retriever()
    docs = retriever.invoke(f"{company_or_symbol} financials balance sheet income statement revenue P/E EPS")
    if not docs:
        return (
            f"No financial data found for '{company_or_symbol}'. "
            "Ask the user to upload reports or use search_financial_docs with the company name."
        )
    parts = [d.page_content for d in docs]
    return "\n\n".join(parts)
