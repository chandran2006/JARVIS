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

# ── TTS worker — runs in its own thread, owns its own engine instance ─────────
class _TTSWorker(threading.Thread):
    """Dedicated TTS thread. pyttsx3 engine lives here — never touches the GUI thread."""

    def __init__(self):
        super().__init__(daemon=True, name="TTS-Worker")
        self._queue   = []
        self._lock    = threading.Lock()
        self._event   = threading.Event()
        self._speaking = False
        self._engine  = None
        self.start()

    def run(self):
        # Create engine inside this thread
        self._engine = pyttsx3.init()
        self._engine.setProperty("rate",   160)
        self._engine.setProperty("volume", 1.0)
        self._pick_voice()

        while True:
            self._event.wait()
            self._event.clear()
            while True:
                with self._lock:
                    if not self._queue:
                        break
                    text = self._queue.pop(0)
                self._speaking = True
                try:
                    self._engine.say(text)
                    self._engine.runAndWait()
                except Exception as e:
                    print(f"[TTS Error] {e}", flush=True)
                finally:
                    self._speaking = False

    def _pick_voice(self):
        voices = self._engine.getProperty("voices")
        for kw in ["david", "mark", "george", "daniel"]:
            for v in voices:
                if kw in v.name.lower():
                    self._engine.setProperty("voice", v.id)
                    return
        if voices:
            self._engine.setProperty("voice", voices[0].id)

    def say(self, text: str):
        with self._lock:
            self._queue.append(text)
        self._event.set()

    def is_speaking(self) -> bool:
        return self._speaking or bool(self._queue)

    def wait_done(self, timeout: float = 30):
        deadline = time.time() + timeout
        while self.is_speaking() and time.time() < deadline:
            time.sleep(0.1)

# Single global worker
_worker = _TTSWorker()

# ── public API ────────────────────────────────────────────────────────────────
def speak(text: str):
    """Speak text aloud. Non-blocking — returns immediately, audio plays in background thread."""
    text = _to_speech(str(text)).strip()
    if not text:
        return
    print(f"\nJARVIS: {text}\n", flush=True)

    if sys.platform == "darwin":
        def _say():
            clean = text.replace('"', '\\"').replace("'", "")
            os.system(f'say -r 160 "{clean}"')
        threading.Thread(target=_say, daemon=True).start()
    else:
        _worker.say(text)

def is_speaking() -> bool:
    return _worker.is_speaking()

def wait_until_done():
    """Block until TTS finishes speaking."""
    _worker.wait_done()

# ── listen ────────────────────────────────────────────────────────────────────
def listen(timeout: int = 5, phrase_limit: int = 10) -> str:
    """Record one utterance. Waits for TTS to finish first to avoid echo."""
    # Wait for JARVIS to finish speaking
    waited = 0
    while is_speaking() and waited < 10:
        time.sleep(0.2)
        waited += 0.2

    r = sr.Recognizer()
    r.pause_threshold          = 0.6
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
