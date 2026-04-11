import sys, os, time, traceback
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

with open("timing_out.txt", "w", encoding="utf-8") as f:
    def log(msg): f.write(msg+"\n"); f.flush(); print(msg, flush=True)

    from dotenv import load_dotenv
    load_dotenv()

    # Time each step
    t0 = time.time()
    from core.registry import SkillRegistry
    from core.engine import JarvisEngine
    log(f"Import time: {time.time()-t0:.3f}s")

    t0 = time.time()
    r = SkillRegistry()
    r.load_skills("skills")
    log(f"Skills load time: {time.time()-t0:.3f}s")

    t0 = time.time()
    e = JarvisEngine(r)
    log(f"Engine init time: {time.time()-t0:.3f}s")

    queries = ["hello", "what time is it", "weather", "bitcoin price", "open youtube", "tell me a joke"]
    for q in queries:
        t0 = time.time()
        resp = e.run_conversation(q)
        elapsed = time.time()-t0
        log(f"Query '{q}' -> {elapsed:.3f}s -> {repr(resp[:60])}")

    log("\n--- TTS timing ---")
    from core.voice import speak
    for text in ["Hello sir.", "The time is 10 AM.", "Good morning sir, all systems ready."]:
        t0 = time.time()
        speak(text, block=True)
        log(f"speak({len(text)} chars) -> {time.time()-t0:.3f}s")
