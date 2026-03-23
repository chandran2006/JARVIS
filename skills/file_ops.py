import os
import json
from typing import List, Dict, Any, Callable
from core.skill import Skill

class FileSkill(Skill):
    @property
    def name(self) -> str:
        return "file_skill"

    def get_tools(self) -> List[Dict[str, Any]]:
        return [
            {
                "type": "function",
                "function": {
                    "name": "manage_file",
                    "description": "Create, read, write, or append to files on the Desktop.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "action": {"type": "string", "enum": ["read", "write", "create", "append"]},
                            "filename": {"type": "string"},
                            "content": {"type": "string"}
                        },
                        "required": ["action", "filename"]
                    }
                }
            }
        ]

    def get_functions(self) -> Dict[str, Callable]:
        return {
            "manage_file": self.manage_file
        }

    def manage_file(self, action: str, filename: str, content: str = ""):
        try:
            desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
            filepath = os.path.join(desktop_path, filename)
            
            if action == "read":
                if os.path.exists(filepath):
                    with open(filepath, 'r') as f:
                        data = f.read()
                    return json.dumps({"status": "success", "content": data})
                else:
                    return json.dumps({"error": "File not found."})
            
            elif action in ["write", "create"]:
                with open(filepath, 'w') as f:
                    f.write(content)
                return json.dumps({"status": "success", "message": f"Created {filename}."})
                
            elif action == "append":
                with open(filepath, 'a') as f:
                    f.write("\n" + content)
                return json.dumps({"status": "success", "message": f"Updated {filename}."})
                
        except Exception as e:
            return json.dumps({"error": str(e)})
