import os
import sys
import argparse
import threading
import time
from dotenv import load_dotenv

# Force UTF-8 output on Windows so print never crashes
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

load_dotenv()

if not os.environ.get("GROQ_API_KEY"):
    print("ERROR: GROQ_API_KEY not found. Add it to your .env file.")
    sys.exit(1)

from core.voice import speak, listen, beep
from core.registry import SkillRegistry
from core.engine import JarvisEngine
from gui.app import run_gui, gui_set_status, gui_set_text

# ── wake-word config ──────────────────────────────────────────────────────────
WAKE_WORDS  = ["jarvis", "hey jarvis", "ok jarvis", "yo jarvis", "hey jar", "jar vis"]
DIRECT_CMDS = [
    "open", "search", "play", "set", "create", "write", "read",
    "what", "who", "when", "where", "how", "why", "tell", "show",
    "volume", "weather", "time", "date", "remember", "forget",
    "hello", "hi", "thank",
]
EXIT_WORDS  = ["quit", "exit", "shutdown", "goodbye", "bye"]
# Filler words left behind after stripping wake word
_FILLER     = {"hey", "ok", "yo", "jar", "vis", "jarvi"}

def _clean(query: str) -> str:
    """Strip wake words and leftover filler words."""
    q = query.lower()
    for w in sorted(WAKE_WORDS, key=len, reverse=True):  # longest first
        q = q.replace(w, "")
    # remove any single leftover filler tokens
    tokens = [t for t in q.split() if t not in _FILLER]
    return " ".join(tokens).strip()

def _should_process(query: str) -> bool:
    q = query.lower()
    if any(w in q for w in WAKE_WORDS):
        return True
    if any(q.startswith(c) or f" {c} " in q for c in DIRECT_CMDS):
        return True
    return False

# ── main JARVIS loop ──────────────────────────────────────────────────────────
def jarvis_loop(pause_event: threading.Event, registry: SkillRegistry, text_mode: bool):
    engine = JarvisEngine(registry)

    if text_mode:
        print("\nJARVIS online - text mode. Type your command.\n")
    else:
        speak("JARVIS online. All systems ready.")

    while True:
        if pause_event.is_set():
            time.sleep(0.3)
            continue

        # ── get input ─────────────────────────────────────────────────────────
        if text_mode:
            try:
                raw = input("YOU: ").strip().lower()
            except (EOFError, KeyboardInterrupt):
                break
        else:
            gui_set_status("LISTENING")
            raw = listen()
            gui_set_status("IDLE")

        if not raw or raw == "none":
            time.sleep(0.1)
            continue

        # ── exit ──────────────────────────────────────────────────────────────
        if any(w in raw for w in EXIT_WORDS):
            speak("Shutting down. Goodbye, sir.")
            os._exit(0)

        # ── filter ────────────────────────────────────────────────────────────
        if not _should_process(raw):
            continue

        query = _clean(raw)

        # Wake word alone ("hey jarvis") -> beep + greet + listen for command
        if not query:
            beep()
            speak("Yes sir, I'm listening.")
            gui_set_status("LISTENING")
            raw2 = listen(timeout=6)
            gui_set_status("IDLE")
            if not raw2 or raw2 == "none":
                continue
            query = _clean(raw2)
            if not query:
                continue

        # ── re-check pause ────────────────────────────────────────────────────
        if pause_event.is_set():
            continue

        # ── run AI ────────────────────────────────────────────────────────────
        try:
            print(f"[Thinking] {query}")
            gui_set_status("THINKING")
            response = engine.run_conversation(query)
            if pause_event.is_set():
                gui_set_status("IDLE")
                continue
            if response:
                gui_set_text(response)
                if text_mode:
                    print(f"JARVIS: {response}\n")
                else:
                    gui_set_status("SPEAKING")
                    speak(response)
                    gui_set_status("IDLE")
        except Exception as e:
            msg = "I hit an error processing that, sir."
            print(f"[Loop Error] {e}")
            gui_set_status("IDLE")
            if text_mode:
                print(f"JARVIS: {msg}\n")
            else:
                speak(msg)

# ── entry point ───────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="JARVIS AI Assistant")
    parser.add_argument("--text", action="store_true", help="Text-only mode (no voice)")
    args = parser.parse_args()

    pause_event = threading.Event()
    context     = {"pause_event": pause_event}

    print("\nJARVIS - Loading skills...")
    registry = SkillRegistry()
    skills_dir = os.path.join(os.path.dirname(__file__), "skills")
    registry.load_skills(skills_dir, context=context)

    t = threading.Thread(
        target=jarvis_loop,
        args=(pause_event, registry, args.text),
        daemon=True,
    )
    t.start()

    if args.text:
        t.join()
    else:
        run_gui(pause_event)

if __name__ == "__main__":
    main()
