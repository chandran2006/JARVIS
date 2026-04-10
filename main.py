import os
import sys
import argparse
import threading
import time

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from dotenv import load_dotenv
load_dotenv()

if not os.environ.get("GROQ_API_KEY"):
    print("ERROR: GROQ_API_KEY not found. Add it to your .env file.")
    sys.exit(1)

from core.voice    import speak, listen
from core.registry import SkillRegistry
from core.engine   import JarvisEngine
from gui.app       import run_gui, gui_set_status, gui_set_text

# ── config ────────────────────────────────────────────────────────────────────
WAKE_WORDS = ["jarvis", "hey jarvis", "ok jarvis", "yo jarvis", "hey jar"]
EXIT_WORDS = ["quit", "exit", "shutdown", "goodbye", "bye", "turn off"]
DIRECT_CMDS = [
    "open","close","search","play","stop","set","create","write","read",
    "delete","list","what","who","when","where","how","why","which",
    "tell","show","give","find","get","volume","weather","time","date",
    "day","remember","forget","recall","hello","hi","good morning",
    "good evening","thank","thanks","take screenshot","lock","battery",
    "system","calculate","convert","translate","note","remind",
]
_FILLER = {"hey","ok","yo","jar","vis","jarvi","okay"}

def _clean(q: str) -> str:
    for w in sorted(WAKE_WORDS, key=len, reverse=True):
        q = q.replace(w, "")
    return " ".join(t for t in q.split() if t not in _FILLER).strip()

def _should_process(q: str) -> bool:
    if any(w in q for w in WAKE_WORDS):
        return True
    return any(q.startswith(c) or f" {c} " in f" {q} " for c in DIRECT_CMDS)

# ── main loop ─────────────────────────────────────────────────────────────────
def jarvis_loop(pause_event: threading.Event,
                registry: SkillRegistry,
                text_mode: bool):

    engine = JarvisEngine(registry)

    if text_mode:
        print("\nJARVIS online. Type your command.\n", flush=True)
    else:
        speak("JARVIS online. All systems ready, sir.")

    while True:
        if pause_event.is_set():
            time.sleep(0.3)
            continue

        # get input
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
            time.sleep(0.05)
            continue

        raw = raw.lower().strip()
        print(f"[Heard] {raw}", flush=True)

        # exit
        if any(w in raw for w in EXIT_WORDS):
            speak("Shutting down. Goodbye, sir.")
            os._exit(0)

        # filter
        if not _should_process(raw):
            continue

        query = _clean(raw)

        # wake word alone → greet
        if not query:
            speak("Yes sir, how can I help you?")
            continue

        if pause_event.is_set():
            continue

        # run AI
        print(f"[Thinking] {query}", flush=True)
        gui_set_status("THINKING")

        try:
            response = engine.run_conversation(query)
        except Exception as e:
            print(f"[Engine Error] {e}", flush=True)
            response = "I hit an error processing that, sir. Please try again."

        gui_set_status("IDLE")
        response = response.strip() if response else "I processed that, sir."
        gui_set_text(response)

        if text_mode:
            print(f"JARVIS: {response}\n", flush=True)
        else:
            gui_set_status("SPEAKING")
            speak(response)
            gui_set_status("IDLE")

# ── entry ─────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="JARVIS AI Assistant")
    parser.add_argument("--text", action="store_true", help="Text-only mode")
    args = parser.parse_args()

    pause_event = threading.Event()
    context     = {"pause_event": pause_event}

    print("\nJARVIS - Loading skills...", flush=True)
    registry   = SkillRegistry()
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
