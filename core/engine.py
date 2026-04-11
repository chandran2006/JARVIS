import os
import json
import re
import time
import threading
from groq import Groq
from core.registry import SkillRegistry

# ── Response cache — instant replies for repeated queries ─────────────────────
_cache: dict = {}
_cache_lock = threading.Lock()
CACHE_TTL = 30  # seconds — time/weather change, so keep short

def _cache_get(key: str):
    with _cache_lock:
        entry = _cache.get(key)
        if entry and (time.time() - entry["ts"]) < CACHE_TTL:
            return entry["val"]
    return None

def _cache_set(key: str, val: str):
    # Only cache intent-dispatched results (fast, deterministic)
    with _cache_lock:
        _cache[key] = {"val": val, "ts": time.time()}

SYSTEM_PROMPT = """You are JARVIS — Chandran's personal AI. Brilliant, fast, witty, deeply knowledgeable.

IRON LAWS:
1. Plain spoken English ONLY. Zero markdown, asterisks, bullets, code blocks.
2. NEVER output <function=...> tags, tool names, JSON, or any technical syntax.
3. NEVER say "retrieving", "fetching", "calling", "processing" — speak the result directly.
4. After a tool runs, speak its result in 1-2 natural sentences.
5. Max 2 sentences unless asked for more detail.
6. Use the word "sir" EXACTLY ONCE per reply, at most. Never say "sir" twice.
7. Be warm, witty, confident. You are talking to your creator.
8. Execute every command instantly — never ask for confirmation.
9. For greetings respond warmly and ask how you can help.
10. You have access to real-time stock prices, crypto, forex, weather, news, timers, alarms, unit conversion, translation, and full system control.
11. When asked about stocks, crypto, or markets — always use the finance tools to get live data.
12. When asked to set a timer or alarm — use the productivity tools immediately.
13. You are aware of current events, market conditions, and can perform complex calculations.
14. Never say you cannot access the internet or real-time data — you can, through your tools."""

# ── Intent patterns — ordered most-specific first ─────────────────────────────
_INTENTS = [
    # Time & Date
    (r"^(?:what(?:'s|\s+is)\s+)?(?:the\s+)?(?:current\s+)?time(?:\s+now)?$|^(?:tell\s+(?:me\s+)?)?(?:the\s+)?time$|^time(?:\s+now)?$",
     "get_current_time", lambda m, q: {}),
    (r"^(?:what(?:'s|\s+is)\s+)?(?:the\s+)?(?:current\s+)?date(?:\s+today)?$|^today(?:'s\s+date)?$|^date$",
     "get_current_date", lambda m, q: {}),
    (r"^(?:what\s+)?day(?:\s+is\s+(?:it|today))?$|^day$",
     "get_day_of_week", lambda m, q: {}),
    (r"^(?:current\s+)?date\s+and\s+time$|^datetime$",
     "get_current_datetime", lambda m, q: {}),

    # Screenshot & Photo — before open/create
    (r"^(?:take\s+(?:a\s+)?)?screenshot$|^(?:capture\s+)?(?:the\s+)?screen$",
     "take_screenshot", lambda m, q: {}),
    (r"^(?:take\s+(?:a\s+)?)?(?:photo|picture|selfie)$|^(?:use\s+)?(?:the\s+)?(?:web)?cam$",
     "take_photo", lambda m, q: {}),

    # Lock/Sleep/Shutdown — before open
    (r"^lock(?:\s+(?:the\s+)?(?:screen|pc|computer|system|laptop|device))?$|^(?:lock|secure)\s+(?:the\s+)?(?:screen|pc|computer|system|laptop)$",
     "lock_screen", lambda m, q: {}),
    (r"^(?:unlock|wake\s+up?)(?:\s+(?:the\s+)?(?:screen|pc|computer|system|laptop|device))?$"
     r"|^(?:unlock|wake\s+up)\s+(?:the\s+)?(?:screen|pc|computer|system|laptop)$"
     r"|^(?:please\s+)?unlock(?:\s+(?:the\s+)?(?:screen|pc|computer|system|laptop|device))?$",
     "unlock_screen", lambda m, q: {"password": os.environ.get("WINDOWS_PASSWORD", "")}),
    (r"^(?:shutdown|shut\s+down|power\s+off)(?:\s+(?:the\s+)?(?:pc|computer|system|laptop))?$",
     "shutdown_pc", lambda m, q: {"restart": False}),
    (r"^restart(?:\s+(?:the\s+)?(?:pc|computer|system|laptop))?$",
     "shutdown_pc", lambda m, q: {"restart": True}),
    (r"^(?:sleep|hibernate)(?:\s+(?:the\s+)?(?:pc|computer|system))?$",
     "run_command", lambda m, q: {"command": "rundll32.exe powrprof.dll,SetSuspendState 0,1,0"}),

    # Volume & Brightness
    (r"^mute$", "mute_volume", lambda m, q: {"mute": True}),
    (r"^unmute$", "mute_volume", lambda m, q: {"mute": False}),
    (r"^(?:set\s+)?volume\s+(?:to\s+)?(\d+)$|^volume\s+(\d+)$",
     "set_volume", lambda m, q: {"level": int(next(g for g in m.groups() if g))}),
    (r"^(?:increase|raise|turn\s+up)\s+(?:the\s+)?volume$",
     "set_volume", lambda m, q: {"level": 80}),
    (r"^(?:decrease|lower|turn\s+down)\s+(?:the\s+)?volume$",
     "set_volume", lambda m, q: {"level": 30}),
    (r"^(?:set\s+)?brightness\s+(?:to\s+)?(\d+)$|^brightness\s+(\d+)$",
     "set_brightness", lambda m, q: {"level": int(next(g for g in m.groups() if g))}),

    # System info
    (r"^(?:what(?:'s|\s+is)\s+)?(?:the\s+)?battery(?:\s+(?:level|status|percentage|life))?$",
     "get_battery", lambda m, q: {}),
    (r"^(?:system\s+)?(?:info|status|stats|performance|health|resources)$",
     "get_system_info", lambda m, q: {}),
    (r"^(?:my\s+)?(?:ip|ip\s+address|network\s+address)$",
     "get_ip_address", lambda m, q: {}),
    (r"^(?:empty|clear)\s+(?:the\s+)?(?:recycle\s*bin|trash|bin)$",
     "empty_recycle_bin", lambda m, q: {}),
    (r"^(?:running\s+)?(?:processes|tasks|apps\s+running)$",
     "get_running_processes", lambda m, q: {}),
    (r"^(?:what(?:'s|\s+is)\s+)?(?:in\s+)?(?:my\s+)?clipboard$",
     "get_clipboard", lambda m, q: {}),

    # Files & Folders — before open/close app
    (r"^(?:create|make|new)\s+(?:a\s+)?folder\s+(?:in|on)\s+(?:the\s+)?(?:my\s+)?desktop$",
     "create_folder", lambda m, q: {"folder_name": "New Folder"}),
    (r"^(?:create|make|new)\s+(?:a\s+)?folder(?:\s+(?:called|named))?\s+(.+?)(?:\s+(?:in|on)\s+(?:the\s+)?(?:my\s+)?desktop)?$",
     "create_folder", lambda m, q: {"folder_name": re.sub(r'\s*(?:in|on)\s+(?:the\s+)?(?:my\s+)?desktop\s*$', '', m.group(1), flags=re.I).strip() or "New Folder"}),
    (r"^(?:delete|remove)\s+(?:the\s+)?folder(?:\s+(?:called|named))?\s+(.+)$",
     "delete_folder", lambda m, q: {"folder_name": m.group(1).strip()}),
    (r"^(?:create|make|new)\s+(?:a\s+)?(?:file|text\s+file|document)(?:\s+(?:called|named))?\s+(.+)$",
     "create_file", lambda m, q: {"filename": m.group(1).strip(), "content": ""}),
    (r"^(?:delete|remove)\s+(?:the\s+)?file(?:\s+(?:called|named))?\s+(.+)$",
     "delete_file", lambda m, q: {"filename": m.group(1).strip()}),
    (r"^(?:list|show)\s+(?:desktop\s+)?files$|^(?:what(?:'s|\s+is)\s+on\s+(?:my\s+)?desktop)$",
     "list_desktop_files", lambda m, q: {}),
    (r"^(?:open|read)\s+(?:the\s+)?file\s+(.+)$",
     "open_file", lambda m, q: {"filename": m.group(1).strip()}),
    (r"^rename\s+(.+?)\s+to\s+(.+)$",
     "rename_file", lambda m, q: {"old_name": m.group(1).strip(), "new_name": m.group(2).strip()}),

    # Weather — before open/search
    (r"^(?:weather|temperature|climate)\s+(?:in|of|for|at)\s+(.+)$",
     "get_weather", lambda m, q: {"city": m.group(1).strip()}),
    (r"^(?:weather|temperature)\s+forecast\s+(?:for\s+)?(.+)$",
     "get_weather_forecast", lambda m, q: {"city": m.group(1).strip()}),
    (r"^(?:weather|temperature|climate)$|^(?:local|current|today(?:'s)?)\s+weather$",
     "get_local_weather", lambda m, q: {}),

    # Web & Search
    (r"^(?:search|google|look\s+up|find)\s+(?:for\s+)?(.+)$",
     "search_web", lambda m, q: {"query": m.group(1).strip(), "engine": "google"}),
    (r"^(?:youtube|play|watch|listen\s+to|put\s+on)\s+(.+)$",
     "play_youtube", lambda m, q: {"query": m.group(1).strip()}),
    (r"^(?:open|go\s+to|visit|browse)\s+(https?://\S+|www\.\S+|\w+\.(?:com|in|org|net|io|co)\S*)$",
     "open_website", lambda m, q: {"url": m.group(1).strip()}),
    (r"^(?:wikipedia|wiki)\s+(.+)$",
     "get_wikipedia_summary", lambda m, q: {"topic": m.group(1).strip()}),
    (r"^news(?:\s+(?:about|on|for|from)\s+(.+))?$"
     r"|^(?:latest|top|breaking|world|india|tech(?:nology)?|business|sports?|science|health|entertainment|politics)\s+news$"
     r"|^(?:what(?:'s|\s+is)\s+(?:happening|going\s+on)(?:\s+in\s+the\s+world)?)$",
     "get_top_news", lambda m, q: {
         "category": (
             m.group(1).strip() if m.lastindex and m.group(1)
             else next((w for w in ["world","india","technology","tech","business","sports","science","health","entertainment","politics"] if w in q.lower()), "general")
         )
     }),
    (r"^(?:directions?|route|navigate|maps?)\s+(?:to\s+)?(.+)$",
     "open_website", lambda m, q: {"url": f"https://maps.google.com/?q={m.group(1).strip().replace(' ', '+')}"}),

    # Coding
    (r"^(?:write|create|generate|make)\s+(?:a\s+)?(?:code|program|script|function|class)\s+(?:for\s+|to\s+)?(.+)$",
     "write_code", lambda m, q: {"question": m.group(1).strip()}),
    (r"^(?:code|program|script)\s+(?:for\s+|to\s+)?(.+)$",
     "write_code", lambda m, q: {"question": m.group(1).strip()}),
    (r"^(?:solve|do|complete)\s+(?:this\s+)?(?:coding\s+)?(?:problem|question|task|challenge)?\s*[:\-]?\s*(.+)$",
     "write_code", lambda m, q: {"question": m.group(1).strip()}),
    (r"^(?:fix|debug|correct)\s+(?:this\s+)?(?:code|bug|error)\s*[:\-]?\s*(.*)$",
     "fix_code", lambda m, q: {"code": m.group(1).strip() or "the code in editor"}),
    (r"^(?:optimize|improve|refactor)\s+(?:this\s+)?(?:code)?\s*[:\-]?\s*(.*)$",
     "optimize_code", lambda m, q: {"code": m.group(1).strip() or "the code in editor"}),
    (r"^(?:explain|what\s+does)\s+(?:this\s+)?(?:code)?\s*(?:do)?\s*[:\-]?\s*(.+)$",
     "explain_code", lambda m, q: {"code": m.group(1).strip()}),

    # Apps — after files/web patterns
    (r"^(?:open|launch|start|run)\s+(?:the\s+)?(.+?)(?:\s+in\s+(?:the\s+)?(.+))?$",
     "open_app", lambda m, q: {"app_name": (m.group(1).strip() + " in " + m.group(2).strip()) if m.group(2) else m.group(1).strip()}),
    (r"^(?:close|kill|quit|exit|stop)\s+(?:the\s+)?(.+)$",
     "close_app", lambda m, q: {"app_name": m.group(1).strip()}),

    # Memory
    (r"^remember\s+(?:that\s+)?(?:my\s+)?(.+?)\s+is\s+(.+)$",
     "remember_fact", lambda m, q: {"key": m.group(1).strip(), "value": m.group(2).strip()}),
    (r"^(?:recall|what\s+do\s+you\s+know\s+about)\s+(.+)$",
     "recall_fact", lambda m, q: {"key": m.group(1).strip()}),
    (r"^(?:list|show)\s+(?:my\s+)?memories$",
     "list_memories", lambda m, q: {}),
    (r"^forget\s+(.+)$",
     "forget_fact", lambda m, q: {"key": m.group(1).strip()}),

    # Notes
    (r"^(?:list|show)\s+(?:my\s+)?notes$",
     "list_notes", lambda m, q: {}),
    (r"^(?:read|open)\s+(?:my\s+)?note\s+(.+)$",
     "read_note", lambda m, q: {"title": m.group(1).strip()}),

    # Math — strict numeric only, must come BEFORE the greedy 'what is'
    (r"^(?:calculate|calc|compute)\s+([\d\s\+\-\*\/\(\)\.%\^\(\)]+)$",
     "calculate", lambda m, q: {"expression": m.group(1).strip()}),
    (r"^(\d+(?:\.\d+)?)%\s+of\s+(\d+(?:\.\d+)?)$",
     "advanced_calculate", lambda m, q: {"expression": q}),
    (r"^convert\s+(.+)\s+to\s+(.+)$",
     "unit_convert", lambda m, q: {"value": m.group(1).strip(), "to_unit": m.group(2).strip()}),

    # Finance — crypto (before stock, more specific)
    (r"^(?:price\s+of\s+)?(?:bitcoin|btc|ethereum|eth|dogecoin|doge|solana|sol|bnb|xrp|ripple|cardano|ada|matic|polygon|shib|shiba)(?:\s+(?:price|worth|today|now))?$",
     "get_crypto_price", lambda m, q: {"coin": q.split()[0] if q.split()[0] not in ('price','of') else q.split()[2]}),
    (r"^(?:crypto|cryptocurrency)\s+(?:price\s+(?:of\s+)?)?(.+)$",
     "get_crypto_price", lambda m, q: {"coin": m.group(1).strip()}),

    # Finance — market indices
    (r"^(?:market|markets|stock\s+market)(?:\s+(?:overview|status|today|update|summary))?$",
     "get_market_overview", lambda m, q: {}),
    (r"^(?:nifty|sensex|nasdaq|s&p 500|dow jones|dow)(?:\s+(?:today|now|status|level))?$",
     "get_market_overview", lambda m, q: {}),
    (r"^(?:top\s+)?(?:gainers?|losers?|movers?)(?:\s+today)?$",
     "get_top_gainers_losers", lambda m, q: {}),

    # Finance — commodities (before forex)
    (r"^(?:gold|silver|crude\s+oil|crude|natural\s+gas|copper|platinum)(?:\s+(?:price|today|now|rate))?$",
     "get_commodity_price", lambda m, q: {"commodity": re.sub(r'\s*(price|today|now|rate)$', '', q, flags=re.I).strip()}),

    # Finance — forex (strict currency codes only)
    (r"^(?:exchange\s+rate|forex)\s+(.+?)\s+to\s+(.+)$",
     "get_forex_rate", lambda m, q: {"from_currency": m.group(1).strip(), "to_currency": m.group(2).strip()}),
    (r"^(?:usd|dollar|dollars|euro|euros|eur|gbp|pound|pounds|yen|jpy|inr|rupee|rupees)\s+(?:to|in)\s+(?:usd|dollar|dollars|euro|euros|eur|gbp|pound|pounds|yen|jpy|inr|rupee|rupees)$",
     "get_forex_rate", lambda m, q: {"from_currency": q.split()[0], "to_currency": q.split()[-1]}),

    # Finance — stocks (specific ticker or company name + keyword)
    (r"^(?:stock\s+)?(?:price\s+of\s+|quote\s+for\s+)(.+)$",
     "get_stock_price", lambda m, q: {"symbol": m.group(1).strip()}),
    (r"^(.+?)\s+(?:stock|share|shares)(?:\s+price)?$",
     "get_stock_price", lambda m, q: {"symbol": m.group(1).strip()}),
    (r"^(?:stock\s+)?info(?:rmation)?\s+(?:for|of|on)\s+(.+)$",
     "get_stock_info", lambda m, q: {"symbol": m.group(1).strip()}),

    # Productivity — timers
    (r"^(?:set\s+(?:a\s+)?)?timer\s+(?:for\s+)?(\d+)\s*(?:minute|min|minutes|mins)$",
     "set_timer", lambda m, q: {"duration_seconds": int(m.group(1)) * 60, "label": "Timer"}),
    (r"^(?:set\s+(?:a\s+)?)?timer\s+(?:for\s+)?(\d+)\s*(?:second|sec|seconds|secs)$",
     "set_timer", lambda m, q: {"duration_seconds": int(m.group(1)), "label": "Timer"}),
    (r"^(?:set\s+(?:a\s+)?)?timer\s+(?:for\s+)?(\d+)\s*(?:hour|hr|hours|hrs)$",
     "set_timer", lambda m, q: {"duration_seconds": int(m.group(1)) * 3600, "label": "Timer"}),
    (r"^(?:set\s+(?:an?\s+)?)?alarm\s+(?:at\s+|for\s+)?(.+)$",
     "set_alarm", lambda m, q: {"time_str": m.group(1).strip()}),
    (r"^(?:cancel|stop|clear)\s+(?:the\s+)?(?:timer|alarm)$",
     "cancel_timer", lambda m, q: {}),
    (r"^(?:list|show)\s+(?:my\s+)?(?:timers?|alarms?)$",
     "list_timers", lambda m, q: {}),

    # Productivity — calc (only pure math expressions, NOT natural language)
    (r"^(?:calculate|calc|compute|what\s+is)\s+([-\d\s\+\-\*\/\(\)\.%\^]+)$",
     "advanced_calculate", lambda m, q: {"expression": m.group(1).strip()}),

    # Productivity — word/translate
    (r"^(?:define|definition\s+of|meaning\s+of)\s+(.+)$",
     "word_definition", lambda m, q: {"word": m.group(1).strip()}),
    (r"^what\s+does\s+(.+?)\s+mean$",
     "word_definition", lambda m, q: {"word": m.group(1).strip()}),
    (r"^translate\s+(.+?)\s+(?:to|into)\s+(.+)$",
     "translate_text", lambda m, q: {"text": m.group(1).strip(), "target_language": m.group(2).strip()}),

    # Fun
    (r"^(?:tell\s+(?:me\s+)?(?:a\s+)?)?joke$",
     "get_joke", lambda m, q: {}),
    (r"^(?:flip\s+(?:a\s+)?)?coin$|^heads\s+or\s+tails$",
     "flip_coin", lambda m, q: {}),
    (r"^(?:roll\s+(?:a?\s+)?)?(?:dice|die)$",
     "roll_dice", lambda m, q: {}),
]

_COMPILED_INTENTS = [
    (re.compile(p, re.I), t, a) for p, t, a in _INTENTS
]

_FILLER_RE = re.compile(
    r"^(?:(?:hey|hi|ok|okay)\s+jarvis[,\s]*|jarvis[,\s]+"
    r"|can\s+you\s+(?:please\s+)?|could\s+you\s+(?:please\s+)?"
    r"|please\s+|would\s+you\s+|will\s+you\s+|just\s+"
    r"|i\s+(?:want|need|would\s+like)\s+(?:you\s+to\s+|to\s+)?"
    r"|kindly\s+|go\s+ahead\s+and\s+)",
    re.I
)

_LEAK_RE = re.compile(
    r"<function[^>]*>.*?</function[^>]*>?"   # <function=...>...</function> full block
    r"|</?function(?:_calls?)?[^>]*>?"        # any standalone <function> or </function> tag
    r"|\w+>\{.*?\}</?function[^>]*>?"        # name>{...}</function with or without closing >
    r"|\[(?:TOOL_CALL|FUNCTION_CALL)\].*"    # [TOOL_CALL]...
    r"|`{3}.*?`{3}",                          # ```code blocks```
    re.DOTALL | re.I
)

_BAD_PHRASES = [
    "no operation", "no action was", "nothing was done", "no operation is done",
    "no task was", "no action taken", "i did not perform", "i have not performed",
    "i'll call", "i'm calling", "i will call", "being retrieved", "being fetched",
    "being displayed", "being opened", "being processed", "i am retrieving",
    "let me retrieve", "let me fetch", "i will retrieve", "i will fetch",
]


# ── Keyword → tool group mapping (keeps schema small per request) ─────────────
_TOOL_GROUPS = {
    "weather":    {"get_weather", "get_local_weather", "get_weather_forecast"},
    "stock":      {"get_stock_price", "get_stock_info", "get_market_overview", "get_top_gainers_losers"},
    "crypto":     {"get_crypto_price", "get_market_overview"},
    "market":     {"get_market_overview", "get_stock_price", "get_top_gainers_losers"},
    "forex":      {"get_forex_rate"},
    "currency":   {"get_forex_rate"},
    "gold":       {"get_commodity_price"},
    "silver":     {"get_commodity_price"},
    "oil":        {"get_commodity_price"},
    "timer":      {"set_timer", "cancel_timer", "list_timers"},
    "alarm":      {"set_alarm", "cancel_timer", "list_timers"},
    "calculate":  {"advanced_calculate"},
    "convert":    {"unit_convert"},
    "translate":  {"translate_text"},
    "define":     {"word_definition"},
    "search":     {"search_web", "get_wikipedia_summary", "get_top_news"},
    "news":       {"get_top_news"},
    "world":      {"get_top_news"},
    "india":      {"get_top_news"},
    "politics":   {"get_top_news"},
    "health":     {"get_top_news"},
    "entertainment": {"get_top_news"},
    "breaking":   {"get_top_news"},
    "headlines":  {"get_top_news"},
    "open":       {"open_app", "open_website"},
    "close":      {"close_app"},
    "volume":     {"set_volume", "mute_volume"},
    "brightness": {"set_brightness"},
    "battery":    {"get_battery"},
    "system":     {"get_system_info", "get_battery", "get_ip_address"},
    "screenshot": {"take_screenshot"},
    "file":       {"create_file", "delete_file", "open_file", "list_desktop_files", "rename_file"},
    "folder":     {"create_folder", "delete_folder"},
    "remember":   {"remember_fact", "recall_fact", "list_memories", "forget_fact"},
    "note":       {"list_notes", "read_note"},
    "email":      {"send_email"},
    "whatsapp":   {"send_whatsapp"},
    "photo":      {"take_photo"},
    "joke":       {"get_joke"},
    "coin":       {"flip_coin"},
    "dice":       {"roll_dice"},
    "code":       {"write_code", "fix_code", "optimize_code", "explain_code"},
    "coding":     {"write_code", "fix_code", "optimize_code", "explain_code"},
    "program":    {"write_code"},
    "script":     {"write_code"},
    "function":   {"write_code"},
    "debug":      {"fix_code"},
    "fix":        {"fix_code"},
    "optimize":   {"optimize_code"},
    "play":       {"play_youtube"},
    "watch":      {"play_youtube"},
    "listen":     {"play_youtube"},
}

# Always-available core tools (small set, always included)
_CORE_TOOLS = {
    "get_current_time", "get_current_date", "get_day_of_week",
    "get_current_datetime", "search_web", "open_website", "open_app",
}


class JarvisEngine:
    def __init__(self, registry: SkillRegistry):
        self.registry   = registry
        self.client     = Groq(api_key=os.environ.get("GROQ_API_KEY"))
        self.model      = "llama-3.1-8b-instant"   # fast model first — avoids rate limits
        self.big_model  = "llama-3.3-70b-versatile" # only for complex follow-ups
        self.history    = []
        self.max_turns  = 10
        self._last_call = 0.0
        self._min_gap   = 0.5          # 500 ms between calls — avoids rate limit
        self._lock      = threading.Lock()

    # ── public entry point ────────────────────────────────────────────────────
    def run_conversation(self, prompt: str) -> str:
        # 1. Try fast local intent dispatch first (no API call needed)
        clean  = _FILLER_RE.sub("", prompt).strip()
        result = self._intent_dispatch(clean) or self._intent_dispatch(prompt)
        if result is not None:
            return result

        # 2. Check LLM cache for identical recent queries
        cache_key = prompt.lower().strip()
        cached = _cache_get(cache_key)
        if cached:
            return cached

        # 3. Fall back to LLM with a focused tool subset
        with self._lock:
            self.history.append({"role": "user", "content": prompt})
            self._trim()
            messages = [{"role": "system", "content": SYSTEM_PROMPT}] + self.history

        tools = self._select_tools(prompt)
        try:
            reply = self._call(messages, tools, depth=0)
        except Exception as e:
            reply = self._recover(e)

        reply = self._clean(reply or "I'm here, sir. How can I help?")
        with self._lock:
            self.history.append({"role": "assistant", "content": reply})
            self._trim()
        return reply

    def prewarm(self):
        """Send a silent dummy request to warm up the Groq connection."""
        try:
            self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": "hi"}],
                max_tokens=5,
            )
        except Exception:
            pass

    # ── select only relevant tools (keeps schema under token limit) ───────────
    def _select_tools(self, prompt: str) -> list:
        all_tools = {t["function"]["name"]: t for t in self.registry.get_tools_schema()}
        wanted = set(_CORE_TOOLS)
        low = prompt.lower()
        for kw, names in _TOOL_GROUPS.items():
            if kw in low:
                wanted |= names
        # Cap at 20 tools to stay well within token limits
        selected = []
        for name, tool in all_tools.items():
            if name in wanted:
                selected.append(tool)
        if not selected:
            # Fallback: return core tools only
            selected = [t for n, t in all_tools.items() if n in _CORE_TOOLS]
        return selected[:20]

    # ── intent dispatch (zero API calls) ─────────────────────────────────────
    def _intent_dispatch(self, query: str) -> str | None:
        q = query.strip()
        for regex, tool_name, arg_fn in _COMPILED_INTENTS:
            m = regex.fullmatch(q) or regex.match(q)
            if not m:
                continue
            fn = self.registry.get_function(tool_name)
            if not fn:
                continue
            try:
                args   = arg_fn(m, q)
                result = fn(**args)
                print(f"  [INTENT] {tool_name}({args})", flush=True)
                try:
                    msg = json.loads(result).get("message", "")
                    return msg if msg else "Done, sir."
                except Exception:
                    return str(result)[:300] if result else "Done, sir."
            except Exception as e:
                print(f"  [INTENT ERR] {tool_name}: {e}", flush=True)
                return "I had a small issue with that, sir."
        return None

    # ── LLM call with rate-limit handling ────────────────────────────────────
    def _call(self, messages: list, tools: list, depth: int) -> str:
        if depth > 3:
            return "Done, sir."

        # Enforce minimum gap between API calls
        with self._lock:
            gap = time.time() - self._last_call
            if gap < self._min_gap:
                time.sleep(self._min_gap - gap)
            self._last_call = time.time()

        kwargs = {
            "model":       self.model,
            "messages":    messages,
            "max_tokens":  256,
            "temperature": 0.4,
        }
        if tools:
            kwargs["tools"]       = tools
            kwargs["tool_choice"] = "auto"

        last_err = None
        for attempt in range(3):
            try:
                resp = self.client.chat.completions.create(**kwargs)
                last_err = None
                break
            except Exception as e:
                last_err = e
                err = str(e).lower()
                if "rate_limit" in err:
                    wait = (attempt + 1) * 3
                    print(f"  [RATE LIMIT] waiting {wait}s...", flush=True)
                    time.sleep(wait)
                elif "model" in err or "not found" in err:
                    kwargs["model"] = self.model  # already fast model, just retry
                    time.sleep(1)
                else:
                    raise

        if last_err:
            raise last_err

        msg = resp.choices[0].message
        if not msg.tool_calls:
            return self._clean((msg.content or "I'm here, sir.").strip())

        messages = list(messages) + [msg]
        for tc in msg.tool_calls:
            result = self._run_tool(tc.function.name, tc.function.arguments)
            messages.append({
                "role": "tool", "tool_call_id": tc.id,
                "name": tc.function.name, "content": result,
            })
        return self._call(messages, tools, depth + 1)

    def _run_tool(self, name: str, args_str: str) -> str:
        fn = self.registry.get_function(name)
        if not fn:
            return json.dumps({"error": f"Tool '{name}' not found."})
        try:
            args   = json.loads(args_str) if args_str else {}
            result = fn(**args)
            print(f"  [TOOL] {name}({args}) -> {str(result)[:100]}", flush=True)
            return str(result)
        except Exception as e:
            return json.dumps({"error": str(e)})

    def _clean(self, reply: str) -> str:
        reply = _LEAK_RE.sub("", reply).strip()
        low   = reply.lower()
        for b in _BAD_PHRASES:
            if b in low:
                return "I'm here, sir. What do you need?"
        reply = self._enforce_one_sir(reply)
        return reply if reply else "I'm here, sir."

    @staticmethod
    def _enforce_one_sir(text: str) -> str:
        """Keep only the first 'sir', remove the rest and clean up punctuation."""
        # Split on 'sir' with optional surrounding punctuation/spaces
        parts = re.split(r'(?i)[,\s]*\bsir\b[,\s]*', text)
        if len(parts) <= 2:
            return text  # zero or one sir — nothing to do
        # Rejoin: first part + 'sir' + second part, then drop the rest
        kept = parts[0].rstrip() + ', sir' + ('. ' if parts[1].lstrip().startswith(('.','!','?')) else ' ') + parts[1].lstrip(' ,')
        tail = ' '.join(p.strip(' ,') for p in parts[2:] if p.strip(' ,'))
        result = (kept.rstrip() + (' ' + tail if tail else '')).strip()
        result = re.sub(r'\s+([,\.\?!])', r'\1', result)
        result = re.sub(r',\s*\.', '.', result)
        result = re.sub(r'\s{2,}', ' ', result).strip()
        return result

    def _recover(self, error: Exception) -> str:
        err = str(error).lower()
        print(f"[Engine Error] {error}", flush=True)
        if "rate_limit" in err:
            return "I hit a rate limit, sir. Give me a few seconds and try again."
        if "connection" in err or "network" in err or "timeout" in err:
            return "I can't reach my servers right now, sir. Check your connection."
        if "api_key" in err or "authentication" in err:
            return "There's an issue with my API key, sir."
        return "I ran into a hiccup, sir. Please try again."

    def _trim(self):
        if len(self.history) > self.max_turns * 2:
            self.history = self.history[-(self.max_turns * 2):]

    def clear_history(self):
        self.history.clear()
