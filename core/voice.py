import os
import sys
import json
import time
import threading
import pyttsx3
import speech_recognition as sr

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# ── TTS ───────────────────────────────────────────────────────────────────────
_engine   = pyttsx3.init()
_tts_lock = threading.Lock()
_speaking = False

def _setup_voice():
    _engine.setProperty("rate",   160)
    _engine.setProperty("volume", 1.0)
    voices = _engine.getProperty("voices")
    for kw in ["david", "mark", "george", "daniel"]:
        for v in voices:
            if kw in v.name.lower():
                _engine.setProperty("voice", v.id)
                return
    if voices:
        _engine.setProperty("voice", voices[0].id)

_setup_voice()

# ── JSON → natural speech ─────────────────────────────────────────────────────
def _to_speech(text: str) -> str:
    if "{" not in text:
        return text.strip()
    try:
        d = json.loads(text)
        if "message" in d:
            return str(d["message"]).strip()
        if d.get("status") == "error":
            return d.get("message", "Something went wrong.")
        if "datetime" in d:
            return f"It is {d['datetime']}."
        if "time" in d:
            return f"The current time is {d['time']}."
        if "date" in d:
            return f"Today is {d['date']}."
        if "day" in d:
            return f"Today is {d['day']}."
        if "value" in d:
            return str(d["value"])
        if "memories" in d:
            m = d["memories"]
            if not m:
                return "I have no memories stored yet."
            parts = [f"{k} is {v}" for k, v in list(m.items())[:5]]
            return "Here is what I remember: " + ", ".join(parts) + "."
        if "content" in d:
            c = str(d["content"])
            return c[:300] if len(c) > 300 else c
        if d.get("status") == "success":
            return "Done, sir."
        pairs = [f"{k} is {v}" for k, v in d.items() if k != "status" and v]
        return ". ".join(pairs) if pairs else "Task completed."
    except Exception:
        return text.strip()

# ── speak ─────────────────────────────────────────────────────────────────────
def speak(text: str):
    global _speaking
    text = _to_speech(str(text)).strip()
    if not text:
        return
    print(f"\nJARVIS: {text}\n", flush=True)
    _speaking = True
    try:
        if sys.platform == "darwin":
            clean = text.replace('"', '\\"').replace("'", "")
            os.system(f'say -r 160 "{clean}"')
        else:
            with _tts_lock:
                _engine.say(text)
                _engine.runAndWait()
    except Exception as e:
        print(f"[TTS Error] {e}", flush=True)
    finally:
        _speaking = False

def is_speaking() -> bool:
    return _speaking

# ── listen ────────────────────────────────────────────────────────────────────
def listen(timeout: int = 5, phrase_limit: int = 10) -> str:
    waited = 0
    while _speaking and waited < 8:
        time.sleep(0.2)
        waited += 0.2

    r = sr.Recognizer()
    r.pause_threshold         = 0.6
    r.dynamic_energy_threshold = True

    try:
        with sr.Microphone() as src:
            print("[Listening...]", flush=True)
            r.adjust_for_ambient_noise(src, duration=0.3)
            audio = r.listen(src, timeout=timeout, phrase_time_limit=phrase_limit)
        print("[Recognising...]", flush=True)
        text = r.recognize_google(audio, language="en-IN")
        print(f"YOU: {text}", flush=True)
        return text.lower().strip()
    except sr.WaitTimeoutError:
        return "none"
    except sr.UnknownValueError:
        return "none"
    except sr.RequestError as e:
        print(f"[Speech API] {e}", flush=True)
        return "none"
    except Exception as e:
        print(f"[Listen Error] {e}", flush=True)
        return "none"
