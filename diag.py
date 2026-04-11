import sys, os, traceback, time

with open("diag_out.txt", "w", encoding="utf-8") as f:

    # 1. TTS test
    f.write("=== TTS TEST ===\n")
    try:
        import pyttsx3
        engine = pyttsx3.init()
        voices = engine.getProperty("voices")
        f.write(f"Voices: {len(voices)}\n")
        for v in voices:
            f.write(f"  {v.name} | {v.id}\n")
        engine.setProperty("rate", 160)
        engine.setProperty("volume", 1.0)
        engine.say("JARVIS TTS test successful")
        engine.runAndWait()
        f.write("TTS: OK\n\n")
    except Exception as ex:
        f.write(f"TTS ERROR: {ex}\n{traceback.format_exc()}\n\n")

    # 2. Microphone test
    f.write("=== MICROPHONE TEST ===\n")
    try:
        import speech_recognition as sr
        r = sr.Recognizer()
        mics = sr.Microphone.list_microphone_names()
        f.write(f"Microphones found: {len(mics)}\n")
        for i, m in enumerate(mics):
            f.write(f"  [{i}] {m}\n")
        f.write("Mic list: OK\n\n")
    except Exception as ex:
        f.write(f"MIC ERROR: {ex}\n{traceback.format_exc()}\n\n")

    # 3. Voice module import
    f.write("=== VOICE MODULE TEST ===\n")
    try:
        from core.voice import speak, listen, is_speaking
        f.write("voice module imported: OK\n")
        speak("Hello sir, JARVIS is online.", block=True)
        f.write("speak() called: OK\n\n")
    except Exception as ex:
        f.write(f"VOICE MODULE ERROR: {ex}\n{traceback.format_exc()}\n\n")

    # 4. Full main loop simulation
    f.write("=== MAIN LOOP SIMULATION ===\n")
    try:
        from dotenv import load_dotenv
        load_dotenv()
        from core.registry import SkillRegistry
        from core.engine import JarvisEngine

        r = SkillRegistry()
        r.load_skills("skills")
        e = JarvisEngine(r)

        test_queries = ["hello", "what time is it", "what is today's date"]
        for q in test_queries:
            try:
                resp = e.run_conversation(q)
                f.write(f"Q: {q}\nA: {resp}\n\n")
                speak(resp, block=True)
                f.write(f"  -> spoken OK\n\n")
            except Exception as ex:
                f.write(f"  -> ERROR on '{q}': {ex}\n{traceback.format_exc()}\n\n")
    except Exception as ex:
        f.write(f"MAIN LOOP ERROR: {ex}\n{traceback.format_exc()}\n\n")

    f.write("=== DONE ===\n")
