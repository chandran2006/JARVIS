from core.skill import Skill
import subprocess
import threading
import sys
import os

class VisionSkill(Skill):
    """
    Skill for launching the standalone Live Vision System.
    """
    
    @property
    def name(self):
        return "vision_skill"
        
    def get_tools(self):
        return [
            {
                "type": "function",
                "function": {
                    "name": "start_live_vision",
                    "description": "Start the live vision system (opens a new window with camera feed and object detection).",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": [],
                    },
                },
            }
        ]

    def get_functions(self):
        return {
            "start_live_vision": self.start_live_vision
        }

    def start_live_vision(self, **kwargs):
        """
        Launches the video_system.py script in a separate process.
        """
        try:
            # Get path to video_system.py (assumed to be in root project dir)
            root_dir = os.path.dirname(os.path.dirname(__file__))
            script_path = os.path.join(root_dir, "video_system.py")
            
            if not os.path.exists(script_path):
                return f"Error: Vision system script not found at {script_path}"

            # Launch process
            # use sys.executable to ensure we use the same python interpreter (venv)
            subprocess.Popen([sys.executable, script_path])
            
            return "Live Vision System started. Check for the new window."
        except Exception as e:
            return f"Error starting vision system: {str(e)}"
