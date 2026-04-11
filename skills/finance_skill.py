import os
import json
import webbrowser
import urllib.parse
from typing import List, Dict, Any, Callable
from core.skill import Skill


class FinanceSkill(Skill):
    @property
    def name(self) -> str:
        return "finance_skill"

    def get_tools(self) -> List[Dict[str, Any]]:
        return [
            {"type": "function", "function": {
                "name": "get_stock_price",
                "description": "Get real-time stock price, change, market cap for any stock symbol or company name (e.g. AAPL, Tesla, RELIANCE, INFY)",
                "parameters": {"type": "object", "properties": {"symbol": {"type": "string", "description": "Stock ticker symbol or company name"}}, "required": ["symbol"]}}},
            {"type": "function", "function": {
                "name": "get_stock_info",
                "description": "Get detailed stock info: P/E ratio, 52-week high/low, volume, market cap, dividend yield",
                "parameters": {"type": "object", "properties": {"symbol": {"type": "string"}}, "required": ["symbol"]}}},
            {"type": "function", "function": {
                "name": "get_crypto_price",
                "description": "Get real-time cryptocurrency price and 24h change (Bitcoin, Ethereum, Dogecoin, etc.)",
                "parameters": {"type": "object", "properties": {"coin": {"type": "string", "description": "Coin name or symbol like BTC, ETH, bitcoin"}}, "required": ["coin"]}}},
            {"type": "function", "function": {
                "name": "get_market_overview",
                "description": "Get overview of major market indices: Nifty 50, Sensex, S&P 500, Nasdaq, Dow Jones",
                "parameters": {"type": "object", "properties": {}, "required": []}}},
            {"type": "function", "function": {
                "name": "get_forex_rate",
                "description": "Get currency exchange rate between two currencies",
                "parameters": {"type": "object", "properties": {
                    "from_currency": {"type": "string", "description": "Source currency code e.g. USD"},
                    "to_currency": {"type": "string", "description": "Target currency code e.g. INR"}
                }, "required": ["from_currency", "to_currency"]}}},
            {"type": "function", "function": {
                "name": "get_top_gainers_losers",
                "description": "Get top gaining and losing stocks in the market today",
                "parameters": {"type": "object", "properties": {"market": {"type": "string", "enum": ["us", "india"], "default": "india"}}, "required": []}}},
            {"type": "function", "function": {
                "name": "get_commodity_price",
                "description": "Get price of commodities like gold, silver, crude oil, natural gas",
                "parameters": {"type": "object", "properties": {"commodity": {"type": "string", "description": "Commodity name: gold, silver, oil, crude, natural gas"}}, "required": ["commodity"]}}},
        ]

    def get_functions(self) -> Dict[str, Callable]:
        return {
            "get_stock_price":       self.get_stock_price,
            "get_stock_info":        self.get_stock_info,
            "get_crypto_price":      self.get_crypto_price,
            "get_market_overview":   self.get_market_overview,
            "get_forex_rate":        self.get_forex_rate,
            "get_top_gainers_losers":self.get_top_gainers_losers,
            "get_commodity_price":   self.get_commodity_price,
        }

    def _yf_fetch(self, symbol: str) -> dict | None:
        """Fetch data from Yahoo Finance API (no key needed)."""
        try:
            import requests
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
            headers = {"User-Agent": "Mozilla/5.0"}
            r = requests.get(url, headers=headers, timeout=6,
                             params={"interval": "1d", "range": "1d"})
            if r.status_code != 200:
                return None
            data = r.json()
            meta = data["chart"]["result"][0]["meta"]
            return meta
        except Exception:
            return None

    def _resolve_symbol(self, symbol: str) -> str:
        """Map common company names to ticker symbols."""
        name_map = {
            "tesla": "TSLA", "apple": "AAPL", "google": "GOOGL", "alphabet": "GOOGL",
            "microsoft": "MSFT", "amazon": "AMZN", "meta": "META", "facebook": "META",
            "netflix": "NFLX", "nvidia": "NVDA", "amd": "AMD", "intel": "INTC",
            "reliance": "RELIANCE.NS", "tcs": "TCS.NS", "infosys": "INFY.NS",
            "infy": "INFY.NS", "wipro": "WIPRO.NS", "hdfc": "HDFCBANK.NS",
            "icici": "ICICIBANK.NS", "sbi": "SBIN.NS", "bajaj": "BAJFINANCE.NS",
            "adani": "ADANIENT.NS", "tatamotors": "TATAMOTORS.NS", "tata motors": "TATAMOTORS.NS",
            "ongc": "ONGC.NS", "itc": "ITC.NS", "hul": "HINDUNILVR.NS",
            "maruti": "MARUTI.NS", "airtel": "BHARTIARTL.NS",
        }
        s = symbol.lower().strip()
        return name_map.get(s, symbol.upper())

    def get_stock_price(self, symbol: str) -> str:
        sym = self._resolve_symbol(symbol)
        meta = self._yf_fetch(sym)
        if meta:
            price = meta.get("regularMarketPrice", 0)
            prev  = meta.get("chartPreviousClose", price)
            change = price - prev
            pct    = (change / prev * 100) if prev else 0
            currency = meta.get("currency", "USD")
            direction = "up" if change >= 0 else "down"
            msg = (f"{sym} is trading at {currency} {price:,.2f}, "
                   f"{direction} {abs(change):.2f} ({abs(pct):.2f}%) today.")
            return json.dumps({"status": "success", "message": msg})
        # Fallback: open finance page
        webbrowser.open(f"https://finance.yahoo.com/quote/{sym}")
        return json.dumps({"status": "success", "message": f"Opened Yahoo Finance for {sym}, sir."})

    def get_stock_info(self, symbol: str) -> str:
        sym = self._resolve_symbol(symbol)
        try:
            import requests
            url = f"https://query1.finance.yahoo.com/v10/finance/quoteSummary/{sym}"
            headers = {"User-Agent": "Mozilla/5.0"}
            r = requests.get(url, headers=headers, timeout=6,
                             params={"modules": "summaryDetail,defaultKeyStatistics"})
            if r.status_code != 200:
                raise Exception("API error")
            result = r.json()["quoteSummary"]["result"][0]
            sd = result.get("summaryDetail", {})
            ks = result.get("defaultKeyStatistics", {})

            def _v(d, k): return d.get(k, {}).get("fmt", "N/A")

            msg = (f"{sym}: Market Cap {_v(sd,'marketCap')}, "
                   f"P/E {_v(sd,'trailingPE')}, "
                   f"52W High {_v(sd,'fiftyTwoWeekHigh')}, "
                   f"52W Low {_v(sd,'fiftyTwoWeekLow')}, "
                   f"Volume {_v(sd,'volume')}, "
                   f"Dividend Yield {_v(sd,'dividendYield')}.")
            return json.dumps({"status": "success", "message": msg})
        except Exception:
            webbrowser.open(f"https://finance.yahoo.com/quote/{sym}")
            return json.dumps({"status": "success", "message": f"Opened detailed info for {sym} in your browser, sir."})

    def get_crypto_price(self, coin: str) -> str:
        coin_map = {
            "bitcoin": "bitcoin", "btc": "bitcoin",
            "ethereum": "ethereum", "eth": "ethereum",
            "dogecoin": "dogecoin", "doge": "dogecoin",
            "solana": "solana", "sol": "solana",
            "cardano": "cardano", "ada": "cardano",
            "ripple": "ripple", "xrp": "ripple",
            "bnb": "binancecoin", "binance": "binancecoin",
            "usdt": "tether", "tether": "tether",
            "shiba": "shiba-inu", "shib": "shiba-inu",
            "polygon": "matic-network", "matic": "matic-network",
        }
        coin_id = coin_map.get(coin.lower(), coin.lower())
        try:
            import requests
            r = requests.get(
                f"https://api.coingecko.com/api/v3/simple/price",
                params={"ids": coin_id, "vs_currencies": "usd,inr",
                        "include_24hr_change": "true"},
                timeout=6)
            if r.status_code == 200:
                data = r.json().get(coin_id, {})
                if data:
                    usd = data.get("usd", 0)
                    inr = data.get("inr", 0)
                    chg = data.get("usd_24h_change", 0)
                    direction = "up" if chg >= 0 else "down"
                    msg = (f"{coin.title()} is at ${usd:,.2f} (₹{inr:,.0f}), "
                           f"{direction} {abs(chg):.2f}% in the last 24 hours.")
                    return json.dumps({"status": "success", "message": msg})
        except Exception:
            pass
        webbrowser.open(f"https://www.coingecko.com/en/coins/{coin_id}")
        return json.dumps({"status": "success", "message": f"Opened CoinGecko for {coin}, sir."})

    def get_market_overview(self) -> str:
        indices = {
            "^NSEI": "Nifty 50",
            "^BSESN": "Sensex",
            "^GSPC": "S&P 500",
            "^IXIC": "Nasdaq",
            "^DJI": "Dow Jones",
        }
        results = []
        try:
            import requests
            headers = {"User-Agent": "Mozilla/5.0"}
            for sym, label in indices.items():
                try:
                    r = requests.get(
                        f"https://query1.finance.yahoo.com/v8/finance/chart/{urllib.parse.quote(sym)}",
                        headers=headers, timeout=4,
                        params={"interval": "1d", "range": "1d"})
                    if r.status_code == 200:
                        meta = r.json()["chart"]["result"][0]["meta"]
                        price = meta.get("regularMarketPrice", 0)
                        prev  = meta.get("chartPreviousClose", price)
                        pct   = ((price - prev) / prev * 100) if prev else 0
                        arrow = "▲" if pct >= 0 else "▼"
                        results.append(f"{label}: {price:,.2f} {arrow}{abs(pct):.2f}%")
                except Exception:
                    continue
        except Exception:
            pass
        if results:
            msg = "Market overview — " + ", ".join(results) + "."
            return json.dumps({"status": "success", "message": msg})
        webbrowser.open("https://finance.yahoo.com/markets/")
        return json.dumps({"status": "success", "message": "Opened market overview in your browser, sir."})

    def get_forex_rate(self, from_currency: str, to_currency: str) -> str:
        try:
            import requests
            pair = f"{from_currency.upper()}{to_currency.upper()}=X"
            meta = self._yf_fetch(pair)
            if meta:
                rate = meta.get("regularMarketPrice", 0)
                msg = f"1 {from_currency.upper()} = {rate:.4f} {to_currency.upper()}."
                return json.dumps({"status": "success", "message": msg})
            # Fallback: exchangerate API (free, no key)
            r = requests.get(
                f"https://api.exchangerate-api.com/v4/latest/{from_currency.upper()}",
                timeout=5)
            if r.status_code == 200:
                rate = r.json()["rates"].get(to_currency.upper(), 0)
                msg = f"1 {from_currency.upper()} = {rate:.4f} {to_currency.upper()}."
                return json.dumps({"status": "success", "message": msg})
        except Exception:
            pass
        return json.dumps({"status": "error", "message": "Could not fetch exchange rate right now, sir."})

    def get_top_gainers_losers(self, market: str = "india") -> str:
        if market == "india":
            webbrowser.open("https://www.nseindia.com/market-data/live-equity-market")
            return json.dumps({"status": "success", "message": "Opened NSE live market data showing top gainers and losers, sir."})
        webbrowser.open("https://finance.yahoo.com/markets/stocks/gainers/")
        return json.dumps({"status": "success", "message": "Opened Yahoo Finance top gainers and losers, sir."})

    def get_commodity_price(self, commodity: str) -> str:
        commodity_map = {
            "gold": "GC=F", "silver": "SI=F",
            "oil": "CL=F", "crude": "CL=F", "crude oil": "CL=F",
            "natural gas": "NG=F", "gas": "NG=F",
            "copper": "HG=F", "platinum": "PL=F",
            "wheat": "ZW=F", "corn": "ZC=F",
        }
        sym = commodity_map.get(commodity.lower(), commodity.upper())
        meta = self._yf_fetch(sym)
        if meta:
            price = meta.get("regularMarketPrice", 0)
            prev  = meta.get("chartPreviousClose", price)
            pct   = ((price - prev) / prev * 100) if prev else 0
            currency = meta.get("currency", "USD")
            direction = "up" if pct >= 0 else "down"
            msg = f"{commodity.title()} is at {currency} {price:,.2f}, {direction} {abs(pct):.2f}% today."
            return json.dumps({"status": "success", "message": msg})
        webbrowser.open(f"https://finance.yahoo.com/quote/{sym}")
        return json.dumps({"status": "success", "message": f"Opened {commodity} price in your browser, sir."})
