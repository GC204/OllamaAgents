"""Live stock data tools via Yahoo Finance (yfinance) - no API key required."""
from langchain_core.tools import tool

try:
    import yfinance as yf
except ImportError:
    yf = None

# Sector ETFs for performance comparison (US markets)
SECTOR_ETFS = {
    "XLK": "Technology",
    "XLF": "Financials",
    "XLV": "Healthcare",
    "XLE": "Energy",
    "XLI": "Industrials",
    "XLP": "Consumer Staples",
    "XLY": "Consumer Discretionary",
    "XLB": "Materials",
    "XLRE": "Real Estate",
    "XLC": "Communication Services",
    "XLU": "Utilities",
}


def _check_yfinance():
    if yf is None:
        return "yfinance is not installed. Run: pip install yfinance"
    return None


@tool
def get_stock_quote(symbol: str) -> str:
    """Get current stock quote: price, change, volume, market cap.
    Use for live price, day change, or quick overview. Symbol examples: AAPL, MSFT, RELIANCE.NS (NSE), TCS.NS."""
    err = _check_yfinance()
    if err:
        return err
    try:
        ticker = yf.Ticker(symbol.upper())
        info = ticker.info
        if not info or info.get("regularMarketPrice") is None:
            return f"No quote found for {symbol}. Check the symbol (e.g. AAPL, MSFT, RELIANCE.NS)."
        price = info.get("regularMarketPrice") or info.get("previousClose")
        change = info.get("regularMarketChange")
        pct = info.get("regularMarketChangePercent")
        vol = info.get("regularMarketVolume")
        cap = info.get("marketCap")
        name = info.get("shortName") or info.get("longName") or symbol
        lines = [
            f"**{name}** ({symbol})",
            f"- Price: {price:.2f}" if isinstance(price, (int, float)) else f"- Price: {price}",
        ]
        if change is not None:
            sign = "+" if change >= 0 else ""
            lines.append(f"- Change: {sign}{change:.2f} ({pct:.2f}%)" if pct is not None else f"- Change: {sign}{change:.2f}")
        if vol:
            lines.append(f"- Volume: {vol:,}")
        if cap:
            lines.append(f"- Market Cap: ${cap/1e9:.2f}B" if cap >= 1e9 else f"- Market Cap: ${cap/1e6:.2f}M")
        return "\n".join(lines)
    except Exception as e:
        return f"Error fetching quote for {symbol}: {e}"


@tool
def get_stock_quotes(symbols: str) -> str:
    """Get current quotes for multiple stocks. Pass comma-separated symbols, e.g. 'RELIANCE.NS, HINDUNILVR.NS, TCS.NS'.
    Use when user asks about several stocks at once (prices, comparison, or dividend/investment across multiple names)."""
    err = _check_yfinance()
    if err:
        return err
    sym_list = [s.strip().upper() for s in symbols.split(",") if s.strip()]
    if not sym_list:
        return "Please provide at least one symbol (comma-separated for multiple)."
    out = []
    for symbol in sym_list:
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            if not info or info.get("regularMarketPrice") is None:
                out.append(f"**{symbol}**: No quote found.")
                continue
            price = info.get("regularMarketPrice") or info.get("previousClose")
            change = info.get("regularMarketChange")
            pct = info.get("regularMarketChangePercent")
            name = info.get("shortName") or info.get("longName") or symbol
            line = f"**{name}** ({symbol}): {price:.2f}"
            if change is not None:
                sign = "+" if change >= 0 else ""
                line += f" ({sign}{change:.2f}, {pct:.2f}%)" if pct is not None else f" ({sign}{change:.2f})"
            out.append(line)
        except Exception as e:
            out.append(f"**{symbol}**: Error - {e}")
    return "\n".join(out)


@tool
def get_dividend_investment(symbol: str, target_dividend: float) -> str:
    """Compute how much to invest in a stock to earn a target annual dividend amount.
    Pass the stock symbol and the target dividend in local currency (e.g. 10000 for 10k).
    Use when user asks 'how much to invest to get X dividend' or 'investment for X yield'."""
    err = _check_yfinance()
    if err:
        return err
    try:
        ticker = yf.Ticker(symbol.upper())
        info = ticker.info
        if not info:
            return f"No data found for {symbol}."
        price = info.get("regularMarketPrice") or info.get("previousClose")
        yield_pct = info.get("dividendYield") or info.get("yield")
        name = info.get("shortName") or info.get("longName") or symbol
        if price is None:
            return f"Could not get price for {symbol}."
        if yield_pct is None or yield_pct <= 0:
            return f"{name} ({symbol}): No dividend yield data. Cannot compute investment for target dividend."
        # yield_pct from yfinance is often decimal (e.g. 0.02 for 2%); sometimes as percentage
        if yield_pct < 1:
            yield_decimal = yield_pct
        else:
            yield_decimal = yield_pct / 100.0
        investment = target_dividend / yield_decimal
        shares = investment / price
        return (
            f"**{name}** ({symbol})\n"
            f"- Target annual dividend: {target_dividend:,.0f}\n"
            f"- Dividend yield: {yield_decimal*100:.2f}%\n"
            f"- Current price: {price:.2f}\n"
            f"- **Investment needed: {investment:,.0f}** (≈ {shares:,.0f} shares)"
        )
    except Exception as e:
        return f"Error for {symbol}: {e}"


@tool
def get_stock_history(symbol: str, period: str = "1mo") -> str:
    """Get historical price data for a stock. Period: 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y.
    Use when user asks for price history, trends, or performance over time."""
    err = _check_yfinance()
    if err:
        return err
    try:
        ticker = yf.Ticker(symbol.upper())
        df = ticker.history(period=period)
        if df.empty or len(df) < 2:
            return f"No history found for {symbol} over {period}."
        start = df["Close"].iloc[0]
        end = df["Close"].iloc[-1]
        high = df["High"].max()
        low = df["Low"].min()
        pct = ((end - start) / start * 100) if start else 0
        lines = [
            f"**{symbol}** ({period})",
            f"- Start: {start:.2f} | End: {end:.2f}",
            f"- High: {high:.2f} | Low: {low:.2f}",
            f"- Return: {pct:+.2f}%",
        ]
        return "\n".join(lines)
    except Exception as e:
        return f"Error fetching history for {symbol}: {e}"


@tool
def get_stock_financials(symbol: str) -> str:
    """Get key financial metrics: P/E, EPS, revenue, profit margin, debt.
    Use when user asks for fundamentals, valuation, or financial health."""
    err = _check_yfinance()
    if err:
        return err
    try:
        ticker = yf.Ticker(symbol.upper())
        info = ticker.info
        if not info:
            return f"No financials found for {symbol}."
        pe = info.get("trailingPE") or info.get("forwardPE")
        eps = info.get("trailingEps") or info.get("forwardEps")
        rev = info.get("totalRevenue")
        profit = info.get("profitMargins")
        debt = info.get("totalDebt")
        roe = info.get("returnOnEquity")
        lines = [f"**{symbol}** – Key metrics"]
        if pe is not None:
            lines.append(f"- P/E: {pe:.2f}")
        if eps is not None:
            lines.append(f"- EPS: {eps:.2f}")
        if rev is not None:
            lines.append(f"- Revenue: ${rev/1e9:.2f}B" if rev >= 1e9 else f"- Revenue: ${rev/1e6:.2f}M")
        if profit is not None:
            lines.append(f"- Profit Margin: {profit*100:.2f}%")
        if debt is not None:
            lines.append(f"- Total Debt: ${debt/1e9:.2f}B" if debt >= 1e9 else f"- Total Debt: ${debt/1e6:.2f}M")
        if roe is not None:
            lines.append(f"- ROE: {roe*100:.2f}%")
        if len(lines) == 1:
            return f"No financial metrics available for {symbol}."
        return "\n".join(lines)
    except Exception as e:
        return f"Error fetching financials for {symbol}: {e}"


@tool
def get_sector_performance() -> str:
    """Get recent performance of major sector ETFs (Technology, Financials, Healthcare, etc.).
    Use when user asks about sector performance, top sectors, or sector comparison."""
    err = _check_yfinance()
    if err:
        return err
    try:
        lines = ["**Sector performance (1 month)**"]
        for sym, name in SECTOR_ETFS.items():
            try:
                ticker = yf.Ticker(sym)
                df = ticker.history(period="1mo")
                if df.empty or len(df) < 2:
                    continue
                start, end = df["Close"].iloc[0], df["Close"].iloc[-1]
                pct = ((end - start) / start * 100) if start else 0
                lines.append(f"- {name} ({sym}): {pct:+.2f}%")
            except Exception:
                continue
        return "\n".join(lines) if len(lines) > 1 else "Could not compute sector performance."
    except Exception as e:
        return f"Error fetching sector performance: {e}"


@tool
def compare_stocks(symbols: str, period: str = "1mo") -> str:
    """Compare multiple stocks over a period. Pass comma-separated symbols, e.g. 'AAPL,MSFT,GOOGL'.
    Use when user wants to compare performance of several stocks."""
    err = _check_yfinance()
    if err:
        return err
    sym_list = [s.strip().upper() for s in symbols.split(",") if s.strip()]
    if not sym_list:
        return "Please provide at least one symbol."
    try:
        lines = [f"**Comparison ({period})**"]
        for sym in sym_list:
            try:
                ticker = yf.Ticker(sym)
                df = ticker.history(period=period)
                if df.empty or len(df) < 2:
                    lines.append(f"- {sym}: N/A")
                    continue
                start, end = df["Close"].iloc[0], df["Close"].iloc[-1]
                pct = ((end - start) / start * 100) if start else 0
                lines.append(f"- {sym}: {pct:+.2f}%")
            except Exception:
                lines.append(f"- {sym}: N/A")
        return "\n".join(lines)
    except Exception as e:
        return f"Error comparing stocks: {e}"
