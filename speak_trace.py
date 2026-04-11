import sys, os, time, traceback
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.stderr.reconfigure(encoding='utf-8', errors='replace')

with open("speak_trace.txt", "w", encoding="utf-8") as f:
    def log(msg):
        f.write(msg + "\n"); f.flush()
        print(msg, flush=True)

    # ── Test 1: raw pyttsx3 ──────────────────────────────────────────────────
    log("=== TEST 1: Raw pyttsx3 ===")
    try:
        import pyttsx3
        e = pyttsx3.init()
        e.setProperty('rate', 160)
        e.setProperty('volume', 1.0)
        voices = e.getProperty('voices')
        log(f"Voices: {[v.name for v in voices]}")
        e.say("Test one. Raw pyttsx3 is working.")
        e.runAndWait()
        log("Raw pyttsx3: OK")
    except Exception as ex:
        log(f"Raw pyttsx3 FAILED: {ex}\n{traceback.format_exc()}")

    # ── Test 2: TTS Worker thread ────────────────────────────────────────────
    log("\n=== TEST 2: TTS Worker (voice.py) ===")
    try:
        from core.voice import speak, _worker
        log(f"Worker alive: {_worker.is_alive()}")
        log(f"Worker busy: {_worker.is_busy()}")
        log("Calling speak('Test two. Voice module working.')...")
        speak("Test two. Voice module working.", block=True)
        log("speak() returned: OK")
    except Exception as ex:
        log(f"voice.py speak FAILED: {ex}\n{traceback.format_exc()}")

    # ── Test 3: _respond function from main ──────────────────────────────────
    log("\n=== TEST 3: _respond from main.py ===")
    try:
        # Import exactly what main.py does
        from core.voice import speak, listen, is_speaking
        from gui.app import gui_set_status, gui_set_text

        def _respond_test(text):
            text = (text or "I'm here, sir.").strip()
            if text.startswith("{"):
                try:
                    import json
                    text = json.loads(text).get("message", text)
                except Exception:
                    pass
            log(f"  _respond text = {repr(text)}")
            try:
                print(f"\nJARVIS: {text}\n", flush=True)
            except Exception as pe:
                log(f"  print failed: {pe}")
            gui_set_text(text)
            gui_set_status("SPEAKING")
            try:
                speak(text, block=True)
                log("  speak() completed OK")
            except Exception as se:
                log(f"  speak() FAILED: {se}\n{traceback.format_exc()}")
            gui_set_status("IDLE")

        _respond_test("Test three. The respond function is working correctly.")
    except Exception as ex:
        log(f"_respond test FAILED: {ex}\n{traceback.format_exc()}")

    # ── Test 4: Full engine + speak chain ────────────────────────────────────
    log("\n=== TEST 4: Engine reply + speak ===")
    try:
        from dotenv import load_dotenv
        load_dotenv()
        from core.registry import SkillRegistry
        from core.engine import JarvisEngine

        r = SkillRegistry()
        r.load_skills("skills")
        engine = JarvisEngine(r)

        for q in ["hello", "what time is it", "tell me a joke"]:
            log(f"\n  Query: '{q}'")
            resp = engine.run_conversation(q)
            log(f"  Reply: {repr(resp)}")
            speak(resp, block=True)
            log(f"  Spoken: OK")
    except Exception as ex:
        log(f"Engine+speak FAILED: {ex}\n{traceback.format_exc()}")

    log("\n=== ALL TESTS DONE ===")
