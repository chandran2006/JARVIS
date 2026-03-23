import os
import json
from typing import List, Dict, Any, Callable
from core.skill import Skill

class SystemSkill(Skill):
    @property
    def name(self) -> str:
        return "system_skill"

    def get_tools(self) -> List[Dict[str, Any]]:
        return [
             {
                "type": "function",
                "function": {
                    "name": "set_volume",
                    "description": "Set system volume (0-100)",
                    "parameters": { "type": "object", "properties": { "level": {"type": "integer"} }, "required": ["level"] }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "open_app",
                    "description": "Open an application on the computer",
                    "parameters": { "type": "object", "properties": { "app_name": {"type": "string"} }, "required": ["app_name"] }
                }
            }
        ]

    def get_functions(self) -> Dict[str, Callable]:
        return {
            "set_volume": self.set_volume,
            "open_app": self.open_app
        }

    # Windows Volume Control using PyCaw
    def set_volume(self, level):
        try:
            # Import here to avoid loading on non-Windows dev environments if checked
            from ctypes import cast, POINTER
            from comtypes import CLSCTX_ALL
            from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
            
            devices = AudioUtilities.GetSpeakers()
            interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
            volume = cast(interface, POINTER(IAudioEndpointVolume))
            
            # Clamp level between 0 and 100
            level = max(0, min(100, int(level)))
            scalar = level / 100.0
            volume.SetMasterVolumeLevelScalar(scalar, None)
            
            return json.dumps({"status": "success", "level": level})
        except ImportError:
             return json.dumps({"error": "PyCaw not installed or not on Windows"})
        except Exception as e:
            return json.dumps({"error": str(e)})

    # Windows App Launching
    def open_app(self, app_name):
        try:
            # Try start command which relies on system PATH and registry
            os.system(f"start {app_name}")
            return json.dumps({"status": "success", "app": app_name})
        except Exception as e:
            return json.dumps({"error": str(e)})
