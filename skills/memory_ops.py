import os
import json
from datetime import datetime
from typing import List, Dict, Any, Callable
from core.skill import Skill

_FILE = os.path.expanduser("~/.jarvis_memory.json")

class MemorySkill(Skill):
    @property
    def name(self) -> str:
        return "memory_skill"

    def _load(self) -> dict:
        try:
            with open(_FILE) as f:
                return json.load(f)
        except Exception:
            return {}

    def _save(self, data: dict):
        with open(_FILE, "w") as f:
            json.dump(data, f, indent=2)

    def get_tools(self) -> List[Dict[str, Any]]:
        return [
            {"type": "function", "function": {
                "name": "remember_fact",
                "description": "Save a fact to long-term memory",
                "parameters": {"type": "object",
                               "properties": {
                                   "key":   {"type": "string"},
                                   "value": {"type": "string"}},
                               "required": ["key", "value"]}}},
            {"type": "function", "function": {
                "name": "recall_fact",
                "description": "Retrieve a saved fact from memory",
                "parameters": {"type": "object",
                               "properties": {"key": {"type": "string"}},
                               "required": ["key"]}}},
            {"type": "function", "function": {
                "name": "list_memories",
                "description": "List all stored memories",
                "parameters": {"type": "object", "properties": {}, "required": []}}},
            {"type": "function", "function": {
                "name": "forget_fact",
                "description": "Delete a memory entry",
                "parameters": {"type": "object",
                               "properties": {"key": {"type": "string"}},
                               "required": ["key"]}}},
        ]

    def get_functions(self) -> Dict[str, Callable]:
        return {
            "remember_fact": self.remember_fact,
            "recall_fact":   self.recall_fact,
            "list_memories": self.list_memories,
            "forget_fact":   self.forget_fact,
        }

    def remember_fact(self, key: str, value: str) -> str:
        mem = self._load()
        mem[key.lower()] = {"value": value, "saved_at": datetime.now().isoformat()}
        self._save(mem)
        return json.dumps({"status": "success",
                           "message": f"Got it, sir. I will remember that {key} is {value}."})

    def recall_fact(self, key: str) -> str:
        entry = self._load().get(key.lower())
        if entry:
            return json.dumps({"status": "success",
                               "message": f"{key} is {entry['value']}."})
        return json.dumps({"status": "not_found",
                           "message": f"I don't have anything stored for {key}."})

    def list_memories(self) -> str:
        mem = self._load()
        if not mem:
            return json.dumps({"status": "success",
                               "message": "I have no memories stored yet, sir."})
        parts = [f"{k} is {v['value']}" for k, v in list(mem.items())[:6]]
        return json.dumps({"status": "success",
                           "message": "Here is what I remember: " + ", ".join(parts) + "."})

    def forget_fact(self, key: str) -> str:
        mem = self._load()
        if key.lower() in mem:
            del mem[key.lower()]
            self._save(mem)
            return json.dumps({"status": "success",
                               "message": f"Done. I have forgotten about {key}."})
        return json.dumps({"status": "not_found",
                           "message": f"I don't have a memory called {key}."})
