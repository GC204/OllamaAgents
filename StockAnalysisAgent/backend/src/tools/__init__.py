from src.tools.rag_tools import search_financial_docs
from src.tools.market_sector_tools import get_market_trends, compare_sectors, get_company_financials
from src.tools.file_analysis_tool import analyze_uploaded_document
from src.tools.live_stock_tools import (
    get_stock_quote,
    get_stock_quotes,
    get_dividend_investment,
    get_stock_history,
    get_stock_financials,
    get_sector_performance,
    compare_stocks,
)

AGENT_TOOLS = [
    search_financial_docs,
    get_market_trends,
    compare_sectors,
    get_company_financials,
    analyze_uploaded_document,
    get_stock_quote,
    get_stock_quotes,
    get_dividend_investment,
    get_stock_history,
    get_stock_financials,
    get_sector_performance,
    compare_stocks,
]

__all__ = [
    "search_financial_docs",
    "get_market_trends",
    "compare_sectors",
    "get_company_financials",
    "analyze_uploaded_document",
    "get_stock_quote",
    "get_stock_quotes",
    "get_dividend_investment",
    "get_stock_history",
    "get_stock_financials",
    "get_sector_performance",
    "compare_stocks",
    "AGENT_TOOLS",
]
