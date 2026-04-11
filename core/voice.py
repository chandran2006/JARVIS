import os
import sys
import json
import threading
import queue
import subprocess
import tempfile
import speech_recognition as sr

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# ── JSON → plain text ─────────────────────────────────────────────────────────
def _to_speech(text: str) -> str:
    text = str(text).strip()
    if not text or "{" not in text:
        return text
    try:
        d = json.loads(text)
        if "message" in d:
            return str(d["message"]).strip()
        if d.get("status") == "error":
            return d.get("message", "Something went wrong.")
        for k in ("datetime", "time", "date", "day", "value", "content"):
            if k in d:
                return str(d[k])
        if d.get("status") == "success":
            return "Done, sir."
        pairs = [f"{k} is {v}" for k, v in d.items() if k != "status" and v]
        return ". ".join(pairs) if pairs else "Done, sir."
    except Exception:
        return text

# ── TTS Worker — runs pyttsx3 in its OWN subprocess, no COM/Qt conflict ───────
_SPEAKER_SCRIPT = """
import sys, pyttsx3
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
text = sys.stdin.read().strip()
if text:
    e = pyttsx3.init()
    e.setProperty('rate', 160)
    e.setProperty('volume', 1.0)
    voices = e.getProperty('voices')
    # Pick David (male) voice
    for v in voices:
        if 'david' in v.name.lower() or 'mark' in v.name.lower():
            e.setProperty('voice', v.id)
            break
    e.say(text)
    e.runAndWait()
"""

class _TTSWorker(threading.Thread):
    def __init__(self):
        super().__init__(daemon=True, name="TTS-Worker")
        self._q       = queue.Queue()
        self._busy    = False
        self._done    = threading.Event()
        self._done.set()
        self.start()

    def run(self):
        while True:
            text = self._q.get()
            if text is None:
                break
            self._busy = True
            self._done.clear()
            try:
                self._speak_subprocess(text)
            except Exception as ex:
                print(f"[TTS] {ex}", flush=True)
            finally:
                self._busy = False
                self._done.set()

    def _speak_subprocess(self, text: str):
        """Speak via a fresh subprocess — completely isolated from Qt/COM."""
        try:
            proc = subprocess.Popen(
                [sys.executable, "-c", _SPEAKER_SCRIPT],
                stdin=subprocess.PIPE,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
            )
            proc.communicate(input=text.encode("utf-8", errors="replace"), timeout=30)
        except subprocess.TimeoutExpired:
            proc.kill()
        except Exception as ex:
            print(f"[TTS subprocess] {ex}", flush=True)

    def say(self, text: str):
        self._done.clear()
        self._q.put(text)

    def is_busy(self) -> bool:
        return self._busy or not self._q.empty()

    def wait(self, timeout: float = 30):
        self._done.wait(timeout=timeout)


_worker = _TTSWorker()

# ── Public API ────────────────────────────────────────────────────────────────
def speak(text: str, block: bool = True):
    text = _to_speech(text).strip()
    if not text:
        return
    try:
        print(f"\nJARVIS: {text}\n", flush=True)
    except Exception:
        pass
    _worker.say(text)
    if block:
        _worker.wait()


def is_speaking() -> bool:
    return _worker.is_busy()


def listen(timeout: int = 7, phrase_limit: int = 12) -> str:
    if is_speaking():
        _worker.wait(timeout=20)

    r = sr.Recognizer()
    r.pause_threshold          = 0.7
    r.non_speaking_duration    = 0.4
    r.dynamic_energy_threshold = True
    r.energy_threshold         = 250

    try:
        with sr.Microphone() as src:
            print("[Listening...]", flush=True)
            r.adjust_for_ambient_noise(src, duration=0.2)
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
