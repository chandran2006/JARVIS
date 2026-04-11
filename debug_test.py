import sys, os, traceback

with open("debug_out.txt", "w", encoding="utf-8") as f:
    try:
        from dotenv import load_dotenv
        load_dotenv()
        from core.registry import SkillRegistry
        from core.engine import JarvisEngine

        r = SkillRegistry()
        r.load_skills("skills")
        e = JarvisEngine(r)

        for q in ["hello", "what time is it", "weather in Chennai", "bitcoin price"]:
            resp = e.run_conversation(q)
            f.write(f"Q: {q}\nA: {resp}\n\n")
            f.flush()

    except Exception as ex:
        f.write(f"ERROR: {ex}\n")
        traceback.print_exc(file=f)
