import os
import json
from datetime import datetime
from typing import List, Dict, Any, Callable
from core.skill import Skill

_MEMORY_FILE = os.path.expanduser("~/.jarvis_memory.json")

class MemorySkill(Skill):
    @property
    def name(self) -> str:
        return "memory_skill"

    # ── helpers ───────────────────────────────────────────────────────────────
    def _load(self) -> dict:
        if not os.path.exists(_MEMORY_FILE):
            return {}
        try:
            with open(_MEMORY_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return {}

    def _save(self, data: dict):
        with open(_MEMORY_FILE, "w") as f:
            json.dump(data, f, indent=2)

    # ── tools ─────────────────────────────────────────────────────────────────
    def get_tools(self) -> List[Dict[str, Any]]:
        return [
            {
                "type": "function",
                "function": {
                    "name": "remember_fact",
                    "description": "Save a fact to long-term memory (e.g. user's name, preference, birthday)",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "key":   {"type": "string", "description": "Short label, e.g. 'my_name'"},
                            "value": {"type": "string", "description": "What to remember"},
                        },
                        "required": ["key", "value"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "recall_fact",
                    "description": "Retrieve a previously saved fact from memory",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "key": {"type": "string"}
                        },
                        "required": ["key"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "list_memories",
                    "description": "List everything stored in memory",
                    "parameters": {"type": "object", "properties": {}, "required": []},
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "forget_fact",
                    "description": "Delete a specific memory entry",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "key": {"type": "string"}
                        },
                        "required": ["key"],
                    },
                },
            },
        ]

    def get_functions(self) -> Dict[str, Callable]:
        return {
            "remember_fact": self.remember_fact,
            "recall_fact":   self.recall_fact,
            "list_memories": self.list_memories,
            "forget_fact":   self.forget_fact,
        }

    # ── implementations ───────────────────────────────────────────────────────
    def remember_fact(self, key: str, value: str) -> str:
        mem = self._load()
        mem[key.lower()] = {"value": value, "saved_at": datetime.now().isoformat()}
        self._save(mem)
        return json.dumps({"status": "success",
                           "message": f"Got it. I'll remember that {key} is {value}."})

    def recall_fact(self, key: str) -> str:
        mem = self._load()
        entry = mem.get(key.lower())
        if entry:
            return json.dumps({"status": "success", "value": entry["value"]})
        return json.dumps({"status": "not_found",
                           "message": f"I don't have anything stored for '{key}'."})

    def list_memories(self) -> str:
        mem = self._load()
        if not mem:
            return json.dumps({"memories": {},
                               "message": "I have no memories stored yet."})
        readable = {k: v["value"] for k, v in mem.items()}
        return json.dumps({"memories": readable})

    def forget_fact(self, key: str) -> str:
        mem = self._load()
        if key.lower() in mem:
            del mem[key.lower()]
            self._save(mem)
            return json.dumps({"status": "success",
                               "message": f"Done. I've forgotten about '{key}'."})
        return json.dumps({"status": "not_found",
                           "message": f"I don't have a memory called '{key}'."})
