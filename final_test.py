import sys, json
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

with open("final_test.txt", "w", encoding="utf-8") as f:
    def log(m): f.write(m+"\n"); f.flush(); print(m, flush=True)

    from dotenv import load_dotenv; load_dotenv()
    from core.registry import SkillRegistry
    r = SkillRegistry()
    r.load_skills("skills")

    # Test play youtube
    play = r.get_function("play_youtube")
    res = json.loads(play("shape of you"))
    log(f"play_youtube: {res['status']} - {res['message']}")

    # Test open website in brave
    ow = r.get_function("open_website")
    res = json.loads(ow("youtube"))
    log(f"open_website(youtube): {res['status']} - {res['message']}")

    # Test search
    sw = r.get_function("search_web")
    res = json.loads(sw("python tutorial", "google"))
    log(f"search_web: {res['status']} - {res['message']}")
