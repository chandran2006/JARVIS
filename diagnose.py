import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from dotenv import load_dotenv
load_dotenv()

print("=== JARVIS DIAGNOSTIC ===", flush=True)

# ── 1. TTS ────────────────────────────────────────────────────────────────────
print("\n[1] Testing TTS...", flush=True)
try:
    import pyttsx3
    e = pyttsx3.init()
    voices = e.getProperty("voices")
    print(f"    Voices found: {len(voices)}", flush=True)
    for v in voices:
        print(f"    - {v.name}", flush=True)
    e.setProperty("rate", 170)
    e.setProperty("voice", voices[0].id)
    e.say("TTS test successful.")
    e.runAndWait()
    print("    TTS OK", flush=True)
except Exception as ex:
    print(f"    TTS FAILED: {ex}", flush=True)

# ── 2. Groq ───────────────────────────────────────────────────────────────────
print("\n[2] Testing Groq API...", flush=True)
try:
    from groq import Groq
    client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
    r = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": "say exactly: hello sir"}],
        max_tokens=20,
    )
    reply = r.choices[0].message.content
    print(f"    Groq reply: {reply}", flush=True)
    e2 = pyttsx3.init()
    e2.setProperty("rate", 170)
    e2.say(reply)
    e2.runAndWait()
    print("    Groq + TTS OK", flush=True)
except Exception as ex:
    print(f"    Groq FAILED: {ex}", flush=True)

# ── 3. Skills + Engine ────────────────────────────────────────────────────────
print("\n[3] Testing Skills + Engine...", flush=True)
try:
    from core.registry import SkillRegistry
    from core.engine import JarvisEngine
    reg = SkillRegistry()
    reg.load_skills(os.path.join(os.path.dirname(__file__), "skills"))
    eng = JarvisEngine(reg)
    resp = eng.run_conversation("what time is it")
    print(f"    Engine response: {resp}", flush=True)
    e3 = pyttsx3.init()
    e3.setProperty("rate", 170)
    e3.say(resp)
    e3.runAndWait()
    print("    Engine + TTS OK", flush=True)
except Exception as ex:
    print(f"    Engine FAILED: {ex}", flush=True)

# ── 4. core/voice.py speak() ─────────────────────────────────────────────────
print("\n[4] Testing core/voice.py speak()...", flush=True)
try:
    from core.voice import speak
    speak("Voice module test. JARVIS is speaking correctly.")
    print("    speak() OK", flush=True)
except Exception as ex:
    print(f"    speak() FAILED: {ex}", flush=True)

print("\n=== DONE ===", flush=True)
