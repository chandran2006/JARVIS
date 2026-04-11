import os
import json
import time
import threading
import webbrowser
from datetime import datetime, timedelta
from typing import List, Dict, Any, Callable
from core.skill import Skill

_timers: Dict[str, threading.Timer] = {}
_speak_fn = None


def _set_speak(fn):
    global _speak_fn
    _speak_fn = fn


def _alert(message: str):
    try:
        if _speak_fn:
            _speak_fn(message, block=False)
        else:
            print(f"\n[ALERT] {message}")
        # Windows toast notification
        try:
            import subprocess
            script = (f'Add-Type -AssemblyName System.Windows.Forms; '
                      f'[System.Windows.Forms.MessageBox]::Show("{message}", "JARVIS Alert")')
            subprocess.Popen(["powershell", "-c", script])
        except Exception:
            pass
    except Exception:
        pass


class ProductivitySkill(Skill):
    @property
    def name(self) -> str:
        return "productivity_skill"

    def initialize(self, context: Dict[str, Any]):
        if "speak" in context:
            _set_speak(context["speak"])

    def get_tools(self) -> List[Dict[str, Any]]:
        return [
            {"type": "function", "function": {
                "name": "set_timer",
                "description": "Set a countdown timer for N minutes or seconds with an optional label",
                "parameters": {"type": "object", "properties": {
                    "duration_seconds": {"type": "integer", "description": "Duration in seconds"},
                    "label": {"type": "string", "description": "Optional timer label", "default": "Timer"}
                }, "required": ["duration_seconds"]}}},
            {"type": "function", "function": {
                "name": "set_alarm",
                "description": "Set an alarm for a specific time like 7:30 AM or 14:00",
                "parameters": {"type": "object", "properties": {
                    "time_str": {"type": "string", "description": "Time string like 7:30 AM or 14:00"},
                    "label": {"type": "string", "default": "Alarm"}
                }, "required": ["time_str"]}}},
            {"type": "function", "function": {
                "name": "cancel_timer",
                "description": "Cancel a running timer or alarm by label",
                "parameters": {"type": "object", "properties": {
                    "label": {"type": "string", "default": "Timer"}
                }, "required": []}}},
            {"type": "function", "function": {
                "name": "list_timers",
                "description": "List all active timers and alarms",
                "parameters": {"type": "object", "properties": {}, "required": []}}},
            {"type": "function", "function": {
                "name": "advanced_calculate",
                "description": "Perform advanced math: algebra, trigonometry, statistics, percentages, compound interest",
                "parameters": {"type": "object", "properties": {
                    "expression": {"type": "string", "description": "Math expression or word problem like '15% of 2500' or 'compound interest 10000 at 8% for 5 years'"}
                }, "required": ["expression"]}}},
            {"type": "function", "function": {
                "name": "unit_convert",
                "description": "Convert between any units: length, weight, temperature, speed, data, area, volume",
                "parameters": {"type": "object", "properties": {
                    "value": {"type": "string", "description": "Value with unit e.g. '100 km' or '5 kg'"},
                    "to_unit": {"type": "string", "description": "Target unit e.g. 'miles' or 'pounds'"}
                }, "required": ["value", "to_unit"]}}},
            {"type": "function", "function": {
                "name": "word_definition",
                "description": "Get definition, synonyms, and pronunciation of any English word",
                "parameters": {"type": "object", "properties": {
                    "word": {"type": "string"}
                }, "required": ["word"]}}},
            {"type": "function", "function": {
                "name": "translate_text",
                "description": "Translate text to any language",
                "parameters": {"type": "object", "properties": {
                    "text": {"type": "string"},
                    "target_language": {"type": "string", "description": "Target language e.g. Spanish, Hindi, French"}
                }, "required": ["text", "target_language"]}}},
            {"type": "function", "function": {
                "name": "get_joke",
                "description": "Tell a random joke",
                "parameters": {"type": "object", "properties": {}, "required": []}}},
            {"type": "function", "function": {
                "name": "flip_coin",
                "description": "Flip a coin — heads or tails",
                "parameters": {"type": "object", "properties": {}, "required": []}}},
            {"type": "function", "function": {
                "name": "roll_dice",
                "description": "Roll one or more dice",
                "parameters": {"type": "object", "properties": {
                    "sides": {"type": "integer", "default": 6},
                    "count": {"type": "integer", "default": 1}
                }, "required": []}}},
        ]

    def get_functions(self) -> Dict[str, Callable]:
        return {
            "set_timer":          self.set_timer,
            "set_alarm":          self.set_alarm,
            "cancel_timer":       self.cancel_timer,
            "list_timers":        self.list_timers,
            "advanced_calculate": self.advanced_calculate,
            "unit_convert":       self.unit_convert,
            "word_definition":    self.word_definition,
            "translate_text":     self.translate_text,
            "get_joke":           self.get_joke,
            "flip_coin":          self.flip_coin,
            "roll_dice":          self.roll_dice,
        }

    def set_timer(self, duration_seconds: int, label: str = "Timer") -> str:
        if label in _timers:
            _timers[label].cancel()
        msg = f"Time's up! {label} is done, sir."
        t = threading.Timer(duration_seconds, _alert, args=[msg])
        t.daemon = True
        t.start()
        _timers[label] = t
        mins, secs = divmod(duration_seconds, 60)
        duration_str = f"{mins} minute{'s' if mins != 1 else ''}" if mins else f"{secs} second{'s' if secs != 1 else ''}"
        if mins and secs:
            duration_str = f"{mins}m {secs}s"
        return json.dumps({"status": "success", "message": f"{label} set for {duration_str}, sir."})

    def set_alarm(self, time_str: str, label: str = "Alarm") -> str:
        try:
            now = datetime.now()
            for fmt in ["%I:%M %p", "%H:%M", "%I %p", "%I:%M:%S %p"]:
                try:
                    alarm_time = datetime.strptime(time_str.upper(), fmt)
                    alarm_time = alarm_time.replace(year=now.year, month=now.month, day=now.day)
                    if alarm_time <= now:
                        alarm_time += timedelta(days=1)
                    break
                except ValueError:
                    continue
            else:
                return json.dumps({"status": "error", "message": f"Could not parse time '{time_str}', sir."})

            delay = (alarm_time - now).total_seconds()
            if label in _timers:
                _timers[label].cancel()
            msg = f"Alarm! {label} — it's {alarm_time.strftime('%I:%M %p')}, sir."
            t = threading.Timer(delay, _alert, args=[msg])
            t.daemon = True
            t.start()
            _timers[label] = t
            return json.dumps({"status": "success",
                               "message": f"{label} set for {alarm_time.strftime('%I:%M %p')}, sir."})
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})

    def cancel_timer(self, label: str = "Timer") -> str:
        if label in _timers:
            _timers[label].cancel()
            del _timers[label]
            return json.dumps({"status": "success", "message": f"{label} cancelled, sir."})
        # Try cancelling all
        if not _timers:
            return json.dumps({"status": "success", "message": "No active timers to cancel, sir."})
        for k, t in list(_timers.items()):
            t.cancel()
        _timers.clear()
        return json.dumps({"status": "success", "message": "All timers cancelled, sir."})

    def list_timers(self) -> str:
        if not _timers:
            return json.dumps({"status": "success", "message": "No active timers or alarms, sir."})
        names = ", ".join(_timers.keys())
        return json.dumps({"status": "success", "message": f"Active timers: {names}."})

    def advanced_calculate(self, expression: str) -> str:
        import math, re
        expr = expression.lower().strip()

        # Compound interest: "compound interest 10000 at 8% for 5 years"
        ci = re.match(r"compound interest\s+([\d.]+)\s+at\s+([\d.]+)%?\s+for\s+([\d.]+)\s+years?", expr)
        if ci:
            p, r, t = float(ci.group(1)), float(ci.group(2)) / 100, float(ci.group(3))
            amount = p * (1 + r) ** t
            interest = amount - p
            return json.dumps({"status": "success",
                               "message": f"Compound interest on {p:,.2f} at {r*100}% for {t} years: "
                                          f"interest = {interest:,.2f}, total = {amount:,.2f}."})

        # Percentage: "15% of 2500"
        pct = re.match(r"([\d.]+)%\s+of\s+([\d.]+)", expr)
        if pct:
            result = float(pct.group(1)) / 100 * float(pct.group(2))
            return json.dumps({"status": "success",
                               "message": f"{pct.group(1)}% of {pct.group(2)} is {result:,.2f}."})

        # Standard math expression
        try:
            safe_expr = re.sub(r"[^0-9+\-*/().%^ ]", "", expression)
            safe_expr = safe_expr.replace("^", "**")
            result = eval(safe_expr, {"__builtins__": {}}, {
                "sin": math.sin, "cos": math.cos, "tan": math.tan,
                "sqrt": math.sqrt, "log": math.log, "pi": math.pi, "e": math.e,
                "abs": abs, "round": round,
            })
            return json.dumps({"status": "success", "message": f"The result is {result:g}."})
        except Exception as e:
            return json.dumps({"status": "error", "message": f"Could not calculate: {e}"})

    def unit_convert(self, value: str, to_unit: str) -> str:
        import re
        m = re.match(r"([\d.]+)\s*(.+)", value.strip())
        if not m:
            return json.dumps({"status": "error", "message": "Invalid value format, sir."})
        num, from_unit = float(m.group(1)), m.group(2).lower().strip()
        to = to_unit.lower().strip()

        conversions = {
            # Length
            ("km", "miles"): 0.621371, ("miles", "km"): 1.60934,
            ("m", "ft"): 3.28084, ("ft", "m"): 0.3048,
            ("cm", "inches"): 0.393701, ("inches", "cm"): 2.54,
            ("m", "yards"): 1.09361, ("yards", "m"): 0.9144,
            # Weight
            ("kg", "lbs"): 2.20462, ("lbs", "kg"): 0.453592,
            ("kg", "pounds"): 2.20462, ("pounds", "kg"): 0.453592,
            ("g", "oz"): 0.035274, ("oz", "g"): 28.3495,
            ("tonnes", "kg"): 1000, ("kg", "tonnes"): 0.001,
            # Speed
            ("kmh", "mph"): 0.621371, ("mph", "kmh"): 1.60934,
            ("km/h", "mph"): 0.621371, ("mph", "km/h"): 1.60934,
            ("m/s", "kmh"): 3.6, ("kmh", "m/s"): 0.277778,
            # Data
            ("gb", "mb"): 1024, ("mb", "gb"): 1/1024,
            ("tb", "gb"): 1024, ("gb", "tb"): 1/1024,
            ("mb", "kb"): 1024, ("kb", "mb"): 1/1024,
            # Area
            ("sqm", "sqft"): 10.7639, ("sqft", "sqm"): 0.092903,
            ("acres", "sqm"): 4046.86, ("sqm", "acres"): 0.000247105,
            ("hectares", "acres"): 2.47105, ("acres", "hectares"): 0.404686,
        }

        # Temperature special case
        if from_unit in ("c", "celsius") and to in ("f", "fahrenheit"):
            result = num * 9/5 + 32
            return json.dumps({"status": "success", "message": f"{num}°C = {result:.2f}°F."})
        if from_unit in ("f", "fahrenheit") and to in ("c", "celsius"):
            result = (num - 32) * 5/9
            return json.dumps({"status": "success", "message": f"{num}°F = {result:.2f}°C."})
        if from_unit in ("c", "celsius") and to in ("k", "kelvin"):
            result = num + 273.15
            return json.dumps({"status": "success", "message": f"{num}°C = {result:.2f}K."})
        if from_unit in ("k", "kelvin") and to in ("c", "celsius"):
            result = num - 273.15
            return json.dumps({"status": "success", "message": f"{num}K = {result:.2f}°C."})

        factor = conversions.get((from_unit, to))
        if factor:
            result = num * factor
            return json.dumps({"status": "success", "message": f"{num} {from_unit} = {result:g} {to}."})
        return json.dumps({"status": "error", "message": f"I don't know how to convert {from_unit} to {to}, sir."})

    def word_definition(self, word: str) -> str:
        try:
            import requests
            r = requests.get(f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}", timeout=5)
            if r.status_code == 200:
                data = r.json()[0]
                meanings = data.get("meanings", [])
                if meanings:
                    part = meanings[0].get("partOfSpeech", "")
                    defn = meanings[0].get("definitions", [{}])[0].get("definition", "")
                    synonyms = meanings[0].get("synonyms", [])[:3]
                    syn_str = f" Synonyms: {', '.join(synonyms)}." if synonyms else ""
                    return json.dumps({"status": "success",
                                       "message": f"{word} ({part}): {defn}{syn_str}"})
        except Exception:
            pass
        webbrowser.open(f"https://www.merriam-webster.com/dictionary/{word}")
        return json.dumps({"status": "success", "message": f"Opened dictionary definition for {word}, sir."})

    def translate_text(self, text: str, target_language: str) -> str:
        # Use MyMemory free translation API
        try:
            import requests
            lang_codes = {
                "hindi": "hi", "spanish": "es", "french": "fr", "german": "de",
                "italian": "it", "portuguese": "pt", "russian": "ru", "japanese": "ja",
                "chinese": "zh", "arabic": "ar", "korean": "ko", "tamil": "ta",
                "telugu": "te", "kannada": "kn", "malayalam": "ml", "bengali": "bn",
                "gujarati": "gu", "marathi": "mr", "punjabi": "pa", "urdu": "ur",
            }
            lang_code = lang_codes.get(target_language.lower(), target_language[:2].lower())
            r = requests.get(
                "https://api.mymemory.translated.net/get",
                params={"q": text, "langpair": f"en|{lang_code}"},
                timeout=6)
            if r.status_code == 200:
                translated = r.json()["responseData"]["translatedText"]
                return json.dumps({"status": "success",
                                   "message": f"In {target_language}: {translated}"})
        except Exception:
            pass
        q = urllib.parse.quote(text) if 'urllib' in dir() else text.replace(" ", "+")
        webbrowser.open(f"https://translate.google.com/?text={q}&tl={target_language[:2]}")
        return json.dumps({"status": "success", "message": f"Opened Google Translate for {target_language}, sir."})

    def get_joke(self) -> str:
        try:
            import requests
            r = requests.get("https://official-joke-api.appspot.com/random_joke", timeout=5)
            if r.status_code == 200:
                d = r.json()
                return json.dumps({"status": "success",
                                   "message": f"{d['setup']} ... {d['punchline']}"})
        except Exception:
            pass
        jokes = [
            "Why don't scientists trust atoms? Because they make up everything.",
            "I told my computer I needed a break. Now it won't stop sending me Kit-Kat ads.",
            "Why do programmers prefer dark mode? Because light attracts bugs.",
        ]
        import random
        return json.dumps({"status": "success", "message": random.choice(jokes)})

    def flip_coin(self) -> str:
        import random
        result = random.choice(["Heads", "Tails"])
        return json.dumps({"status": "success", "message": f"It's {result}, sir."})

    def roll_dice(self, sides: int = 6, count: int = 1) -> str:
        import random
        rolls = [random.randint(1, sides) for _ in range(min(count, 10))]
        total = sum(rolls)
        if count == 1:
            return json.dumps({"status": "success", "message": f"Rolled a {sides}-sided die: {rolls[0]}."})
        return json.dumps({"status": "success",
                           "message": f"Rolled {count} d{sides}: {rolls}, total {total}."})
