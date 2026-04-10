import os
import json
import re
import time
from groq import Groq
from core.registry import SkillRegistry

SYSTEM_PROMPT = """You are JARVIS, an advanced AI assistant — intelligent, concise, and slightly witty like Tony Stark's AI.
Rules:
- Always respond in natural spoken English (no markdown, no bullet points, no asterisks).
- When you use a tool, wait for its result, then give ONE short spoken sentence as your final reply.
- Never expose raw JSON or tool names to the user.
- Be brief: 1-3 sentences max unless the user asks for detail.
- Address the user as "sir" occasionally for personality."""

class JarvisEngine:
    def __init__(self, registry: SkillRegistry):
        self.registry = registry
        self.client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
        self.model = "llama-3.3-70b-versatile"
        self.history = []          # rolling conversation history
        self.max_history = 10      # keep last N user+assistant pairs

    # ── public entry point ────────────────────────────────────────────────────
    def run_conversation(self, user_prompt: str) -> str:
        self.history.append({"role": "user", "content": user_prompt})
        self._trim_history()

        messages = [{"role": "system", "content": SYSTEM_PROMPT}] + self.history
        tools = self.registry.get_tools_schema()

        try:
            reply = self._call(messages, tools, depth=0)
        except Exception as e:
            reply = self._recover(e)

        self.history.append({"role": "assistant", "content": reply})
        self._trim_history()
        return reply

    # ── recursive tool-call handler (max 3 hops) ─────────────────────────────
    def _call(self, messages: list, tools: list, depth: int) -> str:
        if depth > 3:
            return "I've hit my processing limit on that request, sir."

        kwargs = {
            "model": self.model,
            "messages": messages,
            "max_tokens": 300,
            "temperature": 0.6,
        }
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = "auto"

        # Retry once on rate limit with a short wait
        for attempt in range(2):
            try:
                response = self.client.chat.completions.create(**kwargs)
                break
            except Exception as e:
                if "rate_limit" in str(e).lower() and attempt == 0:
                    print("[Rate limit] Waiting 5 seconds...")
                    time.sleep(5)
                else:
                    raise

        msg = response.choices[0].message

        if not msg.tool_calls:
            return msg.content.strip()

        # ── execute every tool call ───────────────────────────────────────────
        messages = messages + [msg]
        for tc in msg.tool_calls:
            result = self._execute_tool(tc.function.name, tc.function.arguments)
            messages.append({
                "role": "tool",
                "tool_call_id": tc.id,
                "name": tc.function.name,
                "content": result,
            })

        return self._call(messages, tools, depth + 1)

    # ── execute a single tool ─────────────────────────────────────────────────
    def _execute_tool(self, name: str, args_str: str) -> str:
        fn = self.registry.get_function(name)
        if not fn:
            return json.dumps({"error": f"Tool '{name}' not found."})
        try:
            args = json.loads(args_str) if args_str else {}
            result = fn(**args)
            print(f"  [TOOL] {name}({args}) -> {str(result)[:120]}")
            return str(result)
        except Exception as e:
            return json.dumps({"error": str(e)})

    # ── error recovery ────────────────────────────────────────────────────────
    def _recover(self, error: Exception) -> str:
        err = str(error)
        # Groq sometimes returns a malformed tool call inside the error body
        m = re.search(r"<function=(\w+).*?(\{.*?\})</function>", err, re.DOTALL)
        if m:
            result = self._execute_tool(m.group(1), m.group(2))
            return result if result else "Task completed, sir."
        if "rate_limit" in err.lower():
            return "I'm being rate-limited right now. Please try again in a moment."
        if "connection" in err.lower():
            return "I can't reach my servers right now. Check your internet connection."
        print(f"[Engine Error] {err}")
        return "I ran into an unexpected issue. Please try again."

    # ── keep history bounded ──────────────────────────────────────────────────
    def _trim_history(self):
        max_msgs = self.max_history * 2
        if len(self.history) > max_msgs:
            self.history = self.history[-max_msgs:]

    def clear_history(self):
        self.history.clear()
