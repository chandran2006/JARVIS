import json
import threading
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any, Callable
from core.skill import Skill


class ReminderSkill(Skill):
    def __init__(self):
        self._reminders: list = []

    @property
    def name(self) -> str:
        return "reminder_skill"

    def get_tools(self) -> List[Dict[str, Any]]:
        return [
            {"type": "function", "function": {
                "name": "set_reminder",
                "description": "Set a reminder to fire after N minutes with a spoken message",
                "parameters": {"type": "object",
                               "properties": {
                                   "message": {"type": "string",
                                               "description": "What to remind about"},
                                   "minutes": {"type": "number",
                                               "description": "How many minutes from now"}},
                               "required": ["message", "minutes"]}}},
            {"type": "function", "function": {
                "name": "set_timer",
                "description": "Start a countdown timer for N minutes or seconds",
                "parameters": {"type": "object",
                               "properties": {
                                   "minutes":  {"type": "number", "default": 0},
                                   "seconds":  {"type": "number", "default": 0},
                                   "label":    {"type": "string", "default": "Timer"}},
                               "required": []}}},
            {"type": "function", "function": {
                "name": "list_reminders",
                "description": "List all pending reminders",
                "parameters": {"type": "object", "properties": {}, "required": []}}},
        ]

    def get_functions(self) -> Dict[str, Callable]:
        return {
            "set_reminder":   self.set_reminder,
            "set_timer":      self.set_timer,
            "list_reminders": self.list_reminders,
        }

    def set_reminder(self, message: str, minutes: float) -> str:
        fire_at = datetime.now() + timedelta(minutes=float(minutes))
        entry   = {"message": message, "fire_at": fire_at, "done": False}
        self._reminders.append(entry)
        threading.Thread(target=self._fire, args=(entry,), daemon=True).start()
        t = fire_at.strftime("%I:%M %p")
        return json.dumps({"status": "success",
                           "message": f"Reminder set for {t}. I will remind you about: {message}."})

    def set_timer(self, minutes: float = 0, seconds: float = 0, label: str = "Timer") -> str:
        total = float(minutes) * 60 + float(seconds)
        if total <= 0:
            return json.dumps({"status": "error", "message": "Please specify a valid duration."})
        threading.Thread(target=self._countdown, args=(total, label), daemon=True).start()
        dur = f"{int(minutes)} minute{'s' if minutes != 1 else ''}" if minutes else f"{int(seconds)} seconds"
        return json.dumps({"status": "success",
                           "message": f"{label} started for {dur}. I will alert you when it is done."})

    def list_reminders(self) -> str:
        pending = [r for r in self._reminders if not r["done"]]
        if not pending:
            return json.dumps({"status": "success", "message": "No pending reminders, sir."})
        parts = [f"{r['message']} at {r['fire_at'].strftime('%I:%M %p')}" for r in pending]
        return json.dumps({"status": "success",
                           "message": "Pending reminders: " + "; ".join(parts) + "."})

    def _fire(self, entry: dict):
        delay = (entry["fire_at"] - datetime.now()).total_seconds()
        if delay > 0:
            time.sleep(delay)
        entry["done"] = True
        try:
            from core.voice import speak
            speak(f"Reminder, sir: {entry['message']}", block=False)
        except Exception:
            print(f"\n[REMINDER] {entry['message']}\n", flush=True)

    def _countdown(self, seconds: float, label: str):
        time.sleep(seconds)
        try:
            from core.voice import speak
            speak(f"{label} is done, sir.", block=False)
        except Exception:
            print(f"\n[TIMER] {label} done!\n", flush=True)
