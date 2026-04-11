import sys, json
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

with open("code_test.txt", "w", encoding="utf-8") as f:
    def log(m): f.write(m+"\n"); f.flush(); print(m, flush=True)

    from dotenv import load_dotenv; load_dotenv()
    from core.registry import SkillRegistry
    r = SkillRegistry()
    r.load_skills("skills")

    # Test coding skill loaded
    wc = r.get_function("write_code")
    ec = r.get_function("explain_code")
    log(f"write_code loaded: {wc is not None}")
    log(f"explain_code loaded: {ec is not None}")

    # Test code generation (no typing)
    res = json.loads(wc("fibonacci sequence", language="python", type_it=False))
    log(f"\nwrite_code result: {res['status']}")
    log(f"Code preview:\n{res['message'][:300]}")

    # Test YouTube autoplay
    py = r.get_function("play_youtube")
    res2 = json.loads(py("shape of you ed sheeran"))
    log(f"\nplay_youtube: {res2['status']} - {res2['message']}")
