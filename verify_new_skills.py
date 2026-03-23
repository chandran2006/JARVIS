import os
import sys
from core.registry import SkillRegistry

def test_skills():
    print("--- Starting Verification ---")
    
    # 1. Initialize Registry
    registry = SkillRegistry()
    skills_dir = os.path.join(os.path.dirname(__file__), "skills")
    print(f"Loading skills from: {skills_dir}")
    registry.load_skills(skills_dir)
    
    # 2. Check Loaded Skills
    loaded_skills = registry.skills.keys()
    print(f"Loaded skills: {list(loaded_skills)}")
    
    required_skills = ["camera_skill", "detection_skill", "whatsapp_skill"]
    missing = [s for s in required_skills if s not in loaded_skills]
    
    if missing:
        print(f"FAILED: Missing skills: {missing}")
        sys.exit(1)
    else:
        print("SUCCESS: All new skills loaded.")

    # 3. Test Camera (Mock or Real)
    print("\n--- Testing Camera Skill ---")
    cam_skill = registry.skills["camera_skill"]
    if hasattr(cam_skill, "take_photo"):
        print("Camera Skill has 'take_photo' method.")
        # We can try calling it, but catch errors if no camera
        try:
            print("Attempting to take photo...")
            result = cam_skill.take_photo()
            print(f"Result: {result}")
        except Exception as e:
            print(f"Camera execution failed (expected if no camera access): {e}")
    else:
        print("FAILED: Camera Skill missing 'take_photo' method.")

    # 4. Test Detection (Mock or Real)
    print("\n--- Testing Detection Skill ---")
    det_skill = registry.skills["detection_skill"]
    if hasattr(det_skill, "detect_objects"):
        print("Detection Skill has 'detect_objects' method.")
        try:
            print("Attempting to load model and detect...")
            # This will check if YOLO loads and MPS is set
            result = det_skill.detect_objects()
            print(f"Result: {result}")
        except Exception as e:
             print(f"Detection execution failed: {e}")
    else:
         print("FAILED: Detection Skill missing 'detect_objects' method.")

    # 5. Test WhatsApp
    print("\n--- Testing WhatsApp Skill ---")
    wa_skill = registry.skills["whatsapp_skill"]
    if hasattr(wa_skill, "send_whatsapp_message"):
        print("WhatsApp Skill has 'send_whatsapp_message' method.")
    else:
        print("FAILED: WhatsApp Skill missing 'send_whatsapp_message' method.")

    print("\n--- Verification Complete ---")

if __name__ == "__main__":
    test_skills()
