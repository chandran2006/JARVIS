
import os
import sys
import subprocess
import threading
from core.skill import Skill
from dotenv import load_dotenv

# Try importing the new SDK
try:
    from google import genai
    HAS_GENAI = True
except ImportError:
    HAS_GENAI = False
    print("Error: google-genai not installed.")

# Audio Configuration
# Managed by gemini_client.py
pass

class GeminiLiveSkill(Skill):
    """
    Skill for connecting to Gemini 2.0 Flash Live API (Multimodal WebSockets).
    Allows real-time video+audio conversation.
    """

    @property
    def name(self):
        return "gemini_live_skill"

    def get_tools(self):
        return [
            {
                "type": "function",
                "function": {
                    "name": "start_live_vision",
                    "description": "Start a live, real-time video and audio conversation with Gemini. Use this when the user wants to 'see' something live or have a continuous conversation.",
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

    def initialize(self, context):
        self.pause_event = context.get("pause_event")

    def start_live_vision(self, **kwargs):
        """
        Launches the gemini_client.py script in a separate process.
        """
        try:
            # Get path to gemini_client.py (assumed to be in root project dir)
            root_dir = os.path.dirname(os.path.dirname(__file__))
            script_path = os.path.join(root_dir, "gemini_client.py")
            
            if not os.path.exists(script_path):
                return f"Error: Gemini client script not found at {script_path}"

            print(f"[GeminiLiveSkill] Launching {script_path}...")
            
            # Pause JARVIS
            if self.pause_event:
                self.pause_event.set()
                print("[GeminiLiveSkill] Paused JARVIS main loop.")

            # Launch process
            # use sys.executable to ensure we use the same python interpreter (venv)
            process = subprocess.Popen([sys.executable, script_path])
            
            # Spawn a thread to wait for the process to finish and then resume JARVIS
            def monitor_process(proc, pause_evt):
                proc.wait()
                if pause_evt:
                    pause_evt.clear()
                    print("[GeminiLiveSkill] Resumed JARVIS main loop.")

            monitor_thread = threading.Thread(target=monitor_process, args=(process, self.pause_event), daemon=True)
            monitor_thread.start()
            
            return "Live Vision System started. I have paused my main listening loop until you close the vision window."
        except Exception as e:
            # Ensure we unpause if launch fails
            if self.pause_event:
                self.pause_event.clear()
            return f"Error starting live vision: {str(e)}"
