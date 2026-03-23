import os
import sys
from core.registry import SkillRegistry

def test_loading():
    print("Testing Skill Loading...")
    registry = SkillRegistry()
    skills_dir = os.path.join(os.path.dirname(__file__), "skills")
    
    print(f"Loading skills from: {skills_dir}")
    registry.load_skills(skills_dir)
    
    print("\nLoaded Skills:")
    for name in registry.skills:
        print(f"- {name}")
        
    print("\nLoaded Tools:")
    for tool in registry.get_tools_schema():
        print(f"- {tool['function']['name']}")
        
    # Check if specific skills are loaded
    expected_skills = ["file_skill", "system_skill", "web_skill"]
    missing = [s for s in expected_skills if s not in registry.skills]
    
    if missing:
        print(f"\nFAILED: Missing skills: {missing}")
        sys.exit(1)
    else:
        print("\nSUCCESS: All core skills loaded.")

if __name__ == "__main__":
    test_loading()
