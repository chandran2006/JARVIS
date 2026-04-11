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

from core.voice    import speak, listen, is_speaking
from core.registry import SkillRegistry
from core.engine   import JarvisEngine
from gui.app       import run_gui, gui_set_status, gui_set_text
from datetime      import datetime

# ── Greeting ──────────────────────────────────────────────────────────────────
def _greeting() -> str:
    h = datetime.now().hour
    if 5  <= h < 12: return "Good morning, sir."
    if 12 <= h < 17: return "Good afternoon, sir."
    if 17 <= h < 21: return "Good evening, sir."
    return "Good night, sir."

# ── Wake words ────────────────────────────────────────────────────────────────
WAKE_WORDS = [
    "hey jarvis", "hai jarvis", "hi jarvis", "ok jarvis",
    "okay jarvis", "yo jarvis", "hey jar", "jarvis",
]
EXIT_WORDS = [
    "shutdown jarvis", "goodbye jarvis", "bye jarvis",
    "turn off jarvis", "stop jarvis", "exit jarvis", "quit jarvis",
    "power off jarvis",
]
_WAKE_SET  = set(WAKE_WORDS)
_FILLER    = {"hey", "hai", "ok", "yo", "jar", "vis", "jarvi", "okay"}
# NOTE: "hi" and "hello" removed from filler — they are valid greetings

def _strip_wake(q: str) -> str:
    original = q
    for w in sorted(WAKE_WORDS, key=len, reverse=True):
        q = q.replace(w, "")
    result = " ".join(t for t in q.split() if t not in _FILLER).strip()
    # If stripping removed everything meaningful, return original minus just "jarvis"
    if not result:
        result = original.replace("jarvis", "").replace("hey", "").replace("hai", "").replace("ok ", "").replace("okay", "").replace("yo ", "").strip()
    return result

def _should_process(q: str) -> bool:
    if any(w in q for w in WAKE_WORDS):
        return True
    words = q.split()
    if len(words) >= 2:   # any 2+ word phrase is likely a command
        return True
    _TRIGGERS = {
        "open","close","search","play","stop","set","create","write","read",
        "delete","list","what","who","when","where","how","why","which","tell",
        "show","find","get","volume","weather","time","date","day","remember",
        "forget","recall","hello","hi","screenshot","lock","battery","system",
        "note","remind","calculate","mute","unmute","brightness","restart",
        "shutdown","music","camera","photo","email","youtube","google","wiki",
        "wikipedia","ip","clipboard","processes","trash","recycle","rename",
        "folder","make","take","check","run","launch","news","maps","route",
        "directions","convert","calc","forecast","sleep","hibernate","unlock","wake",
        # Finance & productivity
        "stock","stocks","market","markets","crypto","bitcoin","btc","ethereum",
        "eth","nifty","sensex","nasdaq","gold","silver","oil","forex","currency",
        "exchange","price","timer","alarm","translate","define","joke","coin",
        "dice","gainers","losers","reliance","tcs","infosys","dogecoin","solana",
    }
    return q in _TRIGGERS or any(q.startswith(c + " ") for c in _TRIGGERS)

# ── Respond ───────────────────────────────────────────────────────────────────
def _respond(text: str, text_mode: bool):
    # Clean up JSON wrapper if engine returned raw JSON
    text = (text or "I'm here, sir.").strip()
    if text.startswith("{"):
        try:
            import json
            text = json.loads(text).get("message", text)
        except Exception:
            pass
    if not text:
        text = "I'm here, sir."

    # Always print to console so you can see it even if TTS fails
    try:
        print(f"\nJARVIS: {text}\n", flush=True)
    except Exception:
        pass

    gui_set_text(text)

    if text_mode:
        pass  # already printed above
    else:
        gui_set_status("SPEAKING")
        try:
            speak(text, block=True)   # unmutes mic internally when done
        except Exception as e:
            print(f"[TTS Error] {e}", flush=True)
            from core.voice import _mic
            _mic.unmute()
        gui_set_status("LISTENING")

# ── Main loop ─────────────────────────────────────────────────────────────────
def jarvis_loop(pause_event: threading.Event,
                registry:    SkillRegistry,
                text_mode:   bool):

    engine = JarvisEngine(registry)

    # Pre-warm Groq connection in background while greeting plays
    threading.Thread(target=engine.prewarm, daemon=True).start()

    _respond(f"{_greeting()} JARVIS online. All systems ready. How can I help you?", text_mode)

    while True:
        if pause_event.is_set():
            time.sleep(0.1)
            continue

        # Input
        if text_mode:
            try:
                raw = input("YOU: ").strip().lower()
            except (EOFError, KeyboardInterrupt):
                break
        else:
            gui_set_status("LISTENING")
            raw = listen()   # returns instantly from always-on mic
            if not raw or raw == "none":
                continue
            gui_set_status("IDLE")

        raw = raw.lower().strip()
        print(f"[Heard] {raw}", flush=True)

        # Exit
        if any(w in raw for w in EXIT_WORDS):
            _respond("Shutting down. Goodbye, sir.", text_mode)
            time.sleep(1.5)
            os._exit(0)

        # Filter noise
        if not _should_process(raw):
            continue

        query = _strip_wake(raw)

        # Wake word alone or just "hi" / "hello" with no command
        if not query or query in ("hi", "hello", "hey"):
            _respond(f"{_greeting()} How can I help you, sir?", text_mode)
            continue

        if pause_event.is_set():
            continue

        print(f"[Query] {query}", flush=True)
        gui_set_status("THINKING")

        try:
            response = engine.run_conversation(query)
        except Exception as e:
            print(f"[Engine Error] {e}", flush=True)
            response = "I hit an error, sir. Please try again."

        _respond(response or "Done, sir.", text_mode)

# ── Entry ─────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="JARVIS AI Assistant")
    parser.add_argument("--text", action="store_true", help="Text-only mode")
    args = parser.parse_args()

    pause_event = threading.Event()
    context     = {"pause_event": pause_event, "speak": speak}

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
