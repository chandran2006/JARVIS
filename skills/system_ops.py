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

    def set_volume(self, level):
        try:
            os.system(f"osascript -e 'set volume output volume {level}'")
            return json.dumps({"status": "success", "level": level})
        except Exception as e:
            return json.dumps({"error": str(e)})

    def open_app(self, app_name):
        try:
            os.system(f"open -a '{app_name}'")
            return json.dumps({"status": "success", "app": app_name})
        except Exception as e:
            return json.dumps({"error": str(e)})
