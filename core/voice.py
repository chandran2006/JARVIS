import os
import sys
import json
import time
import threading
import pyttsx3
import speech_recognition as sr

# ── TTS engine (single global instance) ──────────────────────────────────────
_engine = pyttsx3.init()
_engine.setProperty("rate", 170)
_engine.setProperty("volume", 1.0)
_tts_lock = threading.Lock()

def _pick_voice():
    """Pick the best available male voice on this platform."""
    voices = _engine.getProperty("voices")
    preferred = ["david", "mark", "george", "daniel", "zira"]   # zira = female fallback
    for keyword in preferred:
        for v in voices:
            if keyword in v.name.lower():
                _engine.setProperty("voice", v.id)
                return
    if voices:
        _engine.setProperty("voice", voices[0].id)

_pick_voice()

# ── Speaking flag (thread-safe) ───────────────────────────────────────────────
_speaking = False

def is_speaking() -> bool:
    return _speaking

# ── JSON → natural sentence ───────────────────────────────────────────────────
def _extract_speech(text: str) -> str:
    """Convert JSON tool results into a natural spoken sentence."""
    if "{" not in text:
        return text
    try:
        data = json.loads(text)
        if data.get("status") == "error":
            return data.get("message", "Something went wrong.")
        # datetime / time / date
        if "datetime" in data:
            return f"It is {data['datetime']}."
        if "time" in data:
            return f"The current time is {data['time']}."
        if "date" in data:
            return f"Today is {data['date']}."
        # weather
        if "temperature" in data:
            return (
                f"In {data.get('city','your area')} it is {data['temperature']}, "
                f"feels like {data.get('feels_like','unknown')}, "
                f"{data.get('conditions','')}, "
                f"humidity {data.get('humidity','')}, "
                f"wind {data.get('wind_speed','')}."
            )
        # memory
        if "value" in data:
            return str(data["value"])
        if "memories" in data:
            mems = data["memories"]
            if not mems:
                return "I have no memories stored yet."
            parts = [f"{k} is {v}" for k, v in list(mems.items())[:5]]
            return "Here is what I remember: " + ", ".join(parts) + "."
        # file
        if "content" in data:
            content = data["content"]
            return content[:300] if len(content) > 300 else content
        # generic success
        if data.get("status") == "success":
            return data.get("message", "Done.")
        # fallback: dump readable key-values
        pairs = [f"{k}: {v}" for k, v in data.items() if k != "status"]
        return ". ".join(pairs) if pairs else "Task completed."
    except Exception:
        return text

# ── speak ─────────────────────────────────────────────────────────────────────
def speak(text: str):
    """Speak text aloud. Converts JSON results to natural language first."""
    global _speaking
    text = _extract_speech(str(text)).strip()
    if not text:
        return
    print(f"\nJARVIS: {text}\n")
    _speaking = True
    try:
        if sys.platform == "darwin":
            clean = text.replace('"', '\\"').replace("'", "")
            os.system(f'say -r 170 "{clean}"')
        else:
            with _tts_lock:
                _engine.say(text)
                _engine.runAndWait()
    except Exception as e:
        print(f"[TTS Error] {e}")
    finally:
        _speaking = False

# ── beep (acknowledgement tone) ───────────────────────────────────────────────
def beep():
    """Play a short acknowledgement beep so the user knows JARVIS heard them."""
    try:
        if sys.platform == "win32":
            import winsound
            winsound.Beep(880, 120)   # 880 Hz, 120 ms
        elif sys.platform == "darwin":
            os.system("afplay /System/Library/Sounds/Tink.aiff")
        else:
            os.system("paplay /usr/share/sounds/freedesktop/stereo/bell.oga 2>/dev/null || true")
    except Exception:
        pass

# ── listen ────────────────────────────────────────────────────────────────────
def listen(timeout: int = 5, phrase_limit: int = 10) -> str:
    """
    Listen for a voice command.
    Returns the recognised text (lowercase) or 'none'.
    Skips listening while JARVIS is speaking to avoid echo.
    """
    if _speaking:
        time.sleep(0.5)
        return "none"

    r = sr.Recognizer()
    r.pause_threshold = 0.8
    r.energy_threshold = 300
    r.dynamic_energy_threshold = True

    try:
        with sr.Microphone() as source:
            print("[Listening...]")
            r.adjust_for_ambient_noise(source, duration=0.5)
            audio = r.listen(source, timeout=timeout, phrase_time_limit=phrase_limit)

        print("[Recognising...]")
        query = r.recognize_google(audio, language="en-IN")
        print(f"YOU: {query}")
        return query.lower().strip()

    except sr.WaitTimeoutError:
        return "none"
    except sr.UnknownValueError:
        return "none"
    except sr.RequestError as e:
        print(f"[Speech API Error] {e}")
        return "none"
    except Exception as e:
        print(f"[Listen Error] {e}")
        return "none"
