import os
import json
import re
import time
from groq import Groq
from core.registry import SkillRegistry

SYSTEM_PROMPT = """You are JARVIS, Tony Stark's personal AI. You are intelligent, efficient, and slightly witty.

RULES — follow every one, always:
1. Reply in plain spoken English only. Zero markdown, zero asterisks, zero bullet points.
2. After a tool call, give ONE natural sentence using the result. Never show JSON or tool names.
3. Keep replies to 1-3 sentences unless the user explicitly asks for more.
4. Call the user "sir" once per reply for personality.
5. If you cannot do something, say so clearly and offer an alternative.
6. Use conversation history for follow-up questions — you remember everything said this session."""

class JarvisEngine:
    def __init__(self, registry: SkillRegistry):
        self.registry    = registry
        self.client      = Groq(api_key=os.environ.get("GROQ_API_KEY"))
        self.model       = "llama-3.1-8b-instant"
        self.history     = []
        self.max_history = 20
        self._last_call  = 0.0
        self._min_gap    = 1.0

    # ── public ────────────────────────────────────────────────────────────────
    def run_conversation(self, user_prompt: str) -> str:
        self.history.append({"role": "user", "content": user_prompt})
        self._trim()
        messages = [{"role": "system", "content": SYSTEM_PROMPT}] + self.history
        tools    = self.registry.get_tools_schema()
        try:
            reply = self._call(messages, tools, depth=0)
        except Exception as e:
            reply = self._recover(e)
        reply = reply.strip() if reply else "I processed that, sir."
        self.history.append({"role": "assistant", "content": reply})
        self._trim()
        return reply

    # ── recursive tool loop ───────────────────────────────────────────────────
    def _call(self, messages: list, tools: list, depth: int) -> str:
        if depth > 4:
            return "I have reached my processing limit on that request, sir."

        kwargs = {
            "model":       self.model,
            "messages":    messages,
            "max_tokens":  350,
            "temperature": 0.5,
        }
        if tools:
            kwargs["tools"]       = tools
            kwargs["tool_choice"] = "auto"

        # Rate-limit gap
        gap = time.time() - self._last_call
        if gap < self._min_gap:
            time.sleep(self._min_gap - gap)

        # Retry on rate-limit
        for attempt in range(3):
            try:
                self._last_call = time.time()
                response = self.client.chat.completions.create(**kwargs)
                break
            except Exception as e:
                if "rate_limit" in str(e).lower() and attempt < 2:
                    wait = (attempt + 1) * 8
                    print(f"[Rate limit] Waiting {wait}s...", flush=True)
                    time.sleep(wait)
                else:
                    raise

        msg = response.choices[0].message
        if not msg.tool_calls:
            return (msg.content or "Done, sir.").strip()

        messages = list(messages) + [msg]
        for tc in msg.tool_calls:
            result = self._run_tool(tc.function.name, tc.function.arguments)
            messages.append({
                "role": "tool", "tool_call_id": tc.id,
                "name": tc.function.name, "content": result,
            })
        return self._call(messages, tools, depth + 1)

    # ── tool runner ───────────────────────────────────────────────────────────
    def _run_tool(self, name: str, args_str: str) -> str:
        fn = self.registry.get_function(name)
        if not fn:
            return json.dumps({"error": f"Tool '{name}' not found."})
        try:
            args   = json.loads(args_str) if args_str else {}
            result = fn(**args)
            print(f"  [TOOL] {name} -> {str(result)[:120]}", flush=True)
            return str(result)
        except Exception as e:
            return json.dumps({"error": str(e)})

    # ── error recovery ────────────────────────────────────────────────────────
    def _recover(self, error: Exception) -> str:
        err = str(error)
        m = re.search(r"<function=(\w+).*?(\{.*?\})</function>", err, re.DOTALL)
        if m:
            return self._run_tool(m.group(1), m.group(2)) or "Task completed, sir."
        if "rate_limit" in err.lower():
            return "I am being rate-limited, sir. Please try again in a moment."
        if "connection" in err.lower() or "network" in err.lower():
            return "I cannot reach my servers right now. Please check your internet connection."
        print(f"[Engine Error] {err}", flush=True)
        return "I ran into an unexpected issue. Please try again, sir."

    def _trim(self):
        if len(self.history) > self.max_history * 2:
            self.history = self.history[-(self.max_history * 2):]

    def clear_history(self):
        self.history.clear()
