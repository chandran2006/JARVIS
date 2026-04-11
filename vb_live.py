import sys, json
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

with open("vb_live.txt", "w", encoding="utf-8") as f:
    def log(m): f.write(m+"\n"); f.flush(); print(m, flush=True)

    from dotenv import load_dotenv; load_dotenv()
    from core.registry import SkillRegistry
    r = SkillRegistry()
    r.load_skills("skills")

    sv = r.get_function("set_volume")
    sb = r.get_function("set_brightness")
    mv = r.get_function("mute_volume")

    res = json.loads(sv(50))
    log(f"set_volume(50): {res['status']} - {res['message']}")

    res = json.loads(sb(70))
    log(f"set_brightness(70): {res['status']} - {res['message']}")

    res = json.loads(mv(False))
    log(f"mute_volume(False): {res['status']} - {res['message']}")
