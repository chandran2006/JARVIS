import os
import json
import re
import webbrowser
import urllib.parse
import requests
from typing import List, Dict, Any, Callable
from core.skill import Skill

# ── Number to spoken words ────────────────────────────────────────────────────
def _num_to_words(value: float, currency: str = "") -> str:
    """Convert a number to natural spoken words. e.g. 72860 -> 'seventy two thousand eight hundred sixty'"""
    try:
        if value >= 1_00_00_00_000:   # 100 crore+
            v = value / 1_00_00_00_000
            return f"{v:.2f} billion {currency}".strip()
        if value >= 1_00_00_000:       # 1 crore+
            v = value / 1_00_00_000
            s = f"{v:.2f} crore"
        elif value >= 1_00_000:        # 1 lakh+
            v = value / 1_00_000
            s = f"{v:.2f} lakh"
        elif value >= 1_000:
            v = value / 1_000
            s = f"{v:.2f} thousand"
        else:
            s = f"{value:.2f}"
        return f"{s} {currency}".strip() if currency else s
    except Exception:
        return str(value)


def _price_words(value: float, currency_symbol: str = "dollars") -> str:
    """Return a clean spoken price string."""
    if value <= 0:
        return "unavailable"
    if value >= 1_000_000:
        return f"{value/1_000_000:.2f} million {currency_symbol}"
    if value >= 1_000:
        # e.g. 72,860 -> "seventy two thousand eight hundred sixty dollars"
        thousands = int(value) // 1000
        remainder = int(value) % 1000
        s = f"{thousands} thousand"
        if remainder >= 100:
            hundreds = remainder // 100
            rest = remainder % 100
            s += f" {hundreds} hundred"
            if rest:
                s += f" {rest}"
        elif remainder > 0:
            s += f" {remainder}"
        return f"{s} {currency_symbol}"
    return f"{value:.2f} {currency_symbol}"


def _pct_words(pct: float) -> str:
    direction = "up" if pct >= 0 else "down"
    return f"{direction} {abs(pct):.2f} percent"


def _get(url, params=None, timeout=7) -> dict | None:
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(url, params=params, headers=headers, timeout=timeout)
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    return None


class FinanceSkill(Skill):
    @property
    def name(self) -> str:
        return "finance_skill"

    def get_tools(self) -> List[Dict[str, Any]]:
        return [
            {"type": "function", "function": {
                "name": "get_stock_price",
                "description": "Get real-time stock price for any stock symbol or company name",
                "parameters": {"type": "object", "properties": {
                    "symbol": {"type": "string"}}, "required": ["symbol"]}}},
            {"type": "function", "function": {
                "name": "get_stock_info",
                "description": "Get detailed stock info: P/E ratio, 52-week high/low, volume, market cap",
                "parameters": {"type": "object", "properties": {
                    "symbol": {"type": "string"}}, "required": ["symbol"]}}},
            {"type": "function", "function": {
                "name": "get_crypto_price",
                "description": "Get real-time cryptocurrency price (Bitcoin, Ethereum, Dogecoin, etc.)",
                "parameters": {"type": "object", "properties": {
                    "coin": {"type": "string"}}, "required": ["coin"]}}},
            {"type": "function", "function": {
                "name": "get_market_overview",
                "description": "Get live overview of Nifty 50, Sensex, S&P 500, Nasdaq, Dow Jones",
                "parameters": {"type": "object", "properties": {}, "required": []}}},
            {"type": "function", "function": {
                "name": "get_forex_rate",
                "description": "Get live currency exchange rate between two currencies",
                "parameters": {"type": "object", "properties": {
                    "from_currency": {"type": "string"},
                    "to_currency":   {"type": "string"}}, "required": ["from_currency", "to_currency"]}}},
            {"type": "function", "function": {
                "name": "get_commodity_price",
                "description": "Get real-time price of gold, silver, crude oil, natural gas, copper, platinum",
                "parameters": {"type": "object", "properties": {
                    "commodity": {"type": "string"}}, "required": ["commodity"]}}},
            {"type": "function", "function": {
                "name": "get_top_gainers_losers",
                "description": "Get top gaining and losing stocks today",
                "parameters": {"type": "object", "properties": {
                    "market": {"type": "string", "enum": ["us", "india"], "default": "india"}},
                    "required": []}}},
        ]

    def get_functions(self) -> Dict[str, Callable]:
        return {
            "get_stock_price":        self.get_stock_price,
            "get_stock_info":         self.get_stock_info,
            "get_crypto_price":       self.get_crypto_price,
            "get_market_overview":    self.get_market_overview,
            "get_forex_rate":         self.get_forex_rate,
            "get_commodity_price":    self.get_commodity_price,
            "get_top_gainers_losers": self.get_top_gainers_losers,
        }

    # ── helpers ───────────────────────────────────────────────────────────────
    def _resolve_symbol(self, symbol: str) -> str:
        name_map = {
            "tesla": "TSLA", "apple": "AAPL", "google": "GOOGL",
            "alphabet": "GOOGL", "microsoft": "MSFT", "amazon": "AMZN",
            "meta": "META", "facebook": "META", "netflix": "NFLX",
            "nvidia": "NVDA", "amd": "AMD", "intel": "INTC",
            "reliance": "RELIANCE.NS", "tcs": "TCS.NS",
            "infosys": "INFY.NS", "infy": "INFY.NS",
            "wipro": "WIPRO.NS", "hdfc": "HDFCBANK.NS",
            "icici": "ICICIBANK.NS", "sbi": "SBIN.NS",
            "bajaj": "BAJFINANCE.NS", "adani": "ADANIENT.NS",
            "tatamotors": "TATAMOTORS.NS", "tata motors": "TATAMOTORS.NS",
            "ongc": "ONGC.NS", "itc": "ITC.NS",
            "maruti": "MARUTI.NS", "airtel": "BHARTIARTL.NS",
        }
        return name_map.get(symbol.lower().strip(), symbol.upper())

    def _yf(self, symbol: str) -> dict | None:
        data = _get(
            f"https://query1.finance.yahoo.com/v8/finance/chart/{urllib.parse.quote(symbol)}",
            params={"interval": "1d", "range": "1d"}
        )
        if data:
            try:
                return data["chart"]["result"][0]["meta"]
            except Exception:
                pass
        return None

    # ── stock ─────────────────────────────────────────────────────────────────
    def get_stock_price(self, symbol: str) -> str:
        sym = self._resolve_symbol(symbol)
        meta = self._yf(sym)
        if meta:
            price = meta.get("regularMarketPrice", 0)
            prev  = meta.get("chartPreviousClose", price)
            pct   = ((price - prev) / prev * 100) if prev else 0
            cur   = "rupees" if sym.endswith(".NS") or sym.endswith(".BO") else "dollars"
            msg = f"{symbol.title()} is trading at {_price_words(price, cur)}, {_pct_words(pct)} today."
            return json.dumps({"status": "success", "message": msg})
        webbrowser.open(f"https://finance.yahoo.com/quote/{sym}")
        return json.dumps({"status": "success", "message": f"Opened Yahoo Finance for {sym}, sir."})

    def get_stock_info(self, symbol: str) -> str:
        sym = self._resolve_symbol(symbol)
        try:
            data = _get(
                f"https://query1.finance.yahoo.com/v10/finance/quoteSummary/{sym}",
                params={"modules": "summaryDetail,defaultKeyStatistics"}
            )
            result = data["quoteSummary"]["result"][0]
            sd = result.get("summaryDetail", {})
            def _v(d, k): return d.get(k, {}).get("fmt", "N/A")
            msg = (f"{sym}: Market Cap {_v(sd,'marketCap')}, "
                   f"P/E {_v(sd,'trailingPE')}, "
                   f"52-week high {_v(sd,'fiftyTwoWeekHigh')}, "
                   f"low {_v(sd,'fiftyTwoWeekLow')}.")
            return json.dumps({"status": "success", "message": msg})
        except Exception:
            webbrowser.open(f"https://finance.yahoo.com/quote/{sym}")
            return json.dumps({"status": "success", "message": f"Opened stock info for {sym}, sir."})

    # ── crypto ────────────────────────────────────────────────────────────────
    def get_crypto_price(self, coin: str) -> str:
        coin_map = {
            "bitcoin": "bitcoin", "btc": "bitcoin",
            "ethereum": "ethereum", "eth": "ethereum",
            "dogecoin": "dogecoin", "doge": "dogecoin",
            "solana": "solana", "sol": "solana",
            "cardano": "cardano", "ada": "cardano",
            "ripple": "ripple", "xrp": "ripple",
            "bnb": "binancecoin", "binance": "binancecoin",
            "shiba": "shiba-inu", "shib": "shiba-inu",
            "polygon": "matic-network", "matic": "matic-network",
        }
        coin_id = coin_map.get(coin.lower(), coin.lower())
        data = _get(
            "https://api.coingecko.com/api/v3/simple/price",
            params={"ids": coin_id, "vs_currencies": "usd,inr",
                    "include_24hr_change": "true"}
        )
        if data and coin_id in data:
            d   = data[coin_id]
            usd = d.get("usd", 0)
            inr = d.get("inr", 0)
            chg = d.get("usd_24h_change", 0)
            msg = (f"{coin.title()} is at {_price_words(usd, 'dollars')} "
                   f"or {_price_words(inr, 'rupees')}, "
                   f"{_pct_words(chg)} in the last 24 hours.")
            return json.dumps({"status": "success", "message": msg})
        webbrowser.open(f"https://www.coingecko.com/en/coins/{coin_id}")
        return json.dumps({"status": "success", "message": f"Opened CoinGecko for {coin}, sir."})

    # ── market overview ───────────────────────────────────────────────────────
    def get_market_overview(self) -> str:
        indices = {
            "^NSEI":  "Nifty 50",
            "^BSESN": "Sensex",
            "^GSPC":  "S and P 500",
            "^IXIC":  "Nasdaq",
            "^DJI":   "Dow Jones",
        }
        parts = []
        for sym, label in indices.items():
            meta = self._yf(sym)
            if meta:
                price = meta.get("regularMarketPrice", 0)
                prev  = meta.get("chartPreviousClose", price)
                pct   = ((price - prev) / prev * 100) if prev else 0
                direction = "up" if pct >= 0 else "down"
                parts.append(f"{label} is at {price:,.0f}, {direction} {abs(pct):.2f} percent")
        if parts:
            msg = "Market overview. " + ". ".join(parts) + "."
            return json.dumps({"status": "success", "message": msg})
        webbrowser.open("https://finance.yahoo.com/markets/")
        return json.dumps({"status": "success", "message": "Opened market overview in your browser, sir."})

    # ── forex ─────────────────────────────────────────────────────────────────
    def get_forex_rate(self, from_currency: str, to_currency: str) -> str:
        fc = from_currency.upper().strip()
        tc = to_currency.upper().strip()
        # Use exchangerate-api (free, no key needed)
        data = _get(f"https://api.exchangerate-api.com/v4/latest/{fc}")
        if data:
            rate = data.get("rates", {}).get(tc, 0)
            if rate:
                msg = f"1 {fc} equals {rate:.2f} {tc}."
                return json.dumps({"status": "success", "message": msg})
        # Fallback: Yahoo Finance
        meta = self._yf(f"{fc}{tc}=X")
        if meta:
            rate = meta.get("regularMarketPrice", 0)
            msg = f"1 {fc} equals {rate:.4f} {tc}."
            return json.dumps({"status": "success", "message": msg})
        return json.dumps({"status": "error", "message": f"Could not fetch {fc} to {tc} rate, sir."})

    # ── commodities ───────────────────────────────────────────────────────────
    def get_commodity_price(self, commodity: str) -> str:
        c = commodity.lower().strip()

        # ── Gold & Silver: use metals-api free endpoint (goldapi.io fallback) ──
        if c in ("gold", "silver"):
            # Try metals-live via Yahoo Finance spot prices
            # XAU=X is gold spot in USD per troy oz
            # XAG=X is silver spot in USD per troy oz
            sym = "GC=F" if c == "gold" else "SI=F"
            meta = self._yf(sym)
            if meta:
                price = meta.get("regularMarketPrice", 0)
                prev  = meta.get("chartPreviousClose", price)
                pct   = ((price - prev) / prev * 100) if prev else 0
                # Convert to INR
                inr_rate = self._get_usd_inr()
                inr_price = price * inr_rate if inr_rate else 0
                unit = "per troy ounce"
                msg = (f"{c.title()} is at {_price_words(price, 'dollars')} {unit}. "
                       f"That is {_price_words(inr_price, 'rupees')} {unit}. "
                       f"{_pct_words(pct)} today.")
                return json.dumps({"status": "success", "message": msg})

        # ── Crude Oil ──────────────────────────────────────────────────────────
        if c in ("oil", "crude", "crude oil", "brent"):
            # CL=F is WTI crude, BZ=F is Brent
            sym = "BZ=F" if "brent" in c else "CL=F"
            meta = self._yf(sym)
            if meta:
                price = meta.get("regularMarketPrice", 0)
                prev  = meta.get("chartPreviousClose", price)
                pct   = ((price - prev) / prev * 100) if prev else 0
                msg = (f"Crude oil is at {_price_words(price, 'dollars')} per barrel, "
                       f"{_pct_words(pct)} today.")
                return json.dumps({"status": "success", "message": msg})

        # ── Natural Gas ────────────────────────────────────────────────────────
        if c in ("natural gas", "gas"):
            meta = self._yf("NG=F")
            if meta:
                price = meta.get("regularMarketPrice", 0)
                prev  = meta.get("chartPreviousClose", price)
                pct   = ((price - prev) / prev * 100) if prev else 0
                msg = f"Natural gas is at {price:.3f} dollars per MMBtu, {_pct_words(pct)} today."
                return json.dumps({"status": "success", "message": msg})

        # ── Other commodities ──────────────────────────────────────────────────
        sym_map = {
            "copper":   "HG=F",
            "platinum": "PL=F",
            "wheat":    "ZW=F",
            "corn":     "ZC=F",
            "cotton":   "CT=F",
        }
        sym = sym_map.get(c)
        if sym:
            meta = self._yf(sym)
            if meta:
                price = meta.get("regularMarketPrice", 0)
                prev  = meta.get("chartPreviousClose", price)
                pct   = ((price - prev) / prev * 100) if prev else 0
                msg = f"{c.title()} is at {_price_words(price, 'dollars')}, {_pct_words(pct)} today."
                return json.dumps({"status": "success", "message": msg})

        webbrowser.open(f"https://finance.yahoo.com/commodities/")
        return json.dumps({"status": "success", "message": f"Opened commodity prices in your browser, sir."})

    def _get_usd_inr(self) -> float:
        data = _get("https://api.exchangerate-api.com/v4/latest/USD")
        if data:
            return data.get("rates", {}).get("INR", 84.0)
        return 84.0

    # ── gainers/losers ────────────────────────────────────────────────────────
    def get_top_gainers_losers(self, market: str = "india") -> str:
        if market == "india":
            webbrowser.open("https://www.nseindia.com/market-data/live-equity-market")
            return json.dumps({"status": "success",
                               "message": "Opened NSE live market data showing top gainers and losers, sir."})
        webbrowser.open("https://finance.yahoo.com/markets/stocks/gainers/")
        return json.dumps({"status": "success",
                           "message": "Opened Yahoo Finance top gainers and losers, sir."})
