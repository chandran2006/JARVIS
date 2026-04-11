import sys, os, traceback
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

with open("trace_out.txt", "w", encoding="utf-8") as f:
    def log(msg):
        f.write(msg + "\n"); f.flush()
        print(msg, flush=True)

    from dotenv import load_dotenv
    load_dotenv()

    # Simulate exactly what main.py does
    import re

    WAKE_WORDS = ["hey jarvis","hai jarvis","hi jarvis","ok jarvis","okay jarvis","yo jarvis","hey jar","jarvis"]
    EXIT_WORDS = ["shutdown jarvis","goodbye jarvis","bye jarvis","turn off jarvis","stop jarvis","exit jarvis","quit jarvis","power off jarvis"]
    _FILLER = {"hey","hai","ok","yo","jar","vis","jarvi","okay","hi"}

    def _strip_wake(q):
        for w in sorted(WAKE_WORDS, key=len, reverse=True):
            q = q.replace(w, "")
        return " ".join(t for t in q.split() if t not in _FILLER).strip()

    def _should_process(q):
        if any(w in q for w in WAKE_WORDS): return True
        words = q.split()
        if len(words) >= 2: return True
        _TRIGGERS = {"open","close","search","play","stop","set","create","write","read","delete","list","what","who","when","where","how","why","which","tell","show","find","get","volume","weather","time","date","day","remember","forget","recall","hello","hi","screenshot","lock","battery","system","note","remind","calculate","mute","unmute","brightness","restart","shutdown","music","camera","photo","email","youtube","google","wiki","wikipedia","ip","clipboard","processes","trash","recycle","rename","folder","make","take","check","run","launch","news","maps","route","directions","convert","calc","forecast","sleep","hibernate","stock","stocks","market","markets","crypto","bitcoin","btc","ethereum","eth","nifty","sensex","nasdaq","gold","silver","oil","forex","currency","exchange","price","timer","alarm","translate","define","joke","coin","dice","gainers","losers","reliance","tcs","infosys","dogecoin","solana"}
        return q in _TRIGGERS or any(q.startswith(c + " ") for c in _TRIGGERS)

    from core.registry import SkillRegistry
    from core.engine import JarvisEngine

    registry = SkillRegistry()
    registry.load_skills("skills")
    engine = JarvisEngine(registry)

    test_inputs = [
        "jarvis",
        "hello",
        "hey jarvis",
        "hey jarvis what time is it",
        "what time is it",
        "jarvis what is the time",
        "time",
        "what is today",
        "hi",
        "how are you",
        "tell me a joke",
        "weather",
        "open youtube",
    ]

    log("\n=== TRACING MAIN.PY FLOW ===\n")
    for raw in test_inputs:
        log(f"--- INPUT: '{raw}' ---")
        raw_l = raw.lower().strip()

        if any(w in raw_l for w in EXIT_WORDS):
            log("  -> EXIT WORD, skipped"); continue

        should = _should_process(raw_l)
        log(f"  _should_process: {should}")
        if not should:
            log("  -> FILTERED OUT — jarvis never hears this!"); continue

        query = _strip_wake(raw_l)
        log(f"  _strip_wake result: '{query}'")

        if not query:
            log("  -> EMPTY after strip — only greeting sent"); continue

        try:
            resp = engine.run_conversation(query)
            log(f"  ENGINE REPLY: {repr(resp)}")
        except Exception as e:
            log(f"  ENGINE ERROR: {e}")
            traceback.print_exc(file=f)
        log("")
