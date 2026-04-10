import os
import json
from typing import List, Dict, Any, Callable
from core.skill import Skill

_DESKTOP = os.path.join(os.path.expanduser("~"), "Desktop")

class FileSkill(Skill):
    @property
    def name(self) -> str:
        return "file_skill"

    def get_tools(self) -> List[Dict[str, Any]]:
        return [
            {
                "type": "function",
                "function": {
                    "name": "create_file",
                    "description": "Create a new text file on the Desktop with given content",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "filename": {"type": "string"},
                            "content":  {"type": "string"},
                        },
                        "required": ["filename", "content"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "read_file",
                    "description": "Read the contents of a file on the Desktop",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "filename": {"type": "string"}
                        },
                        "required": ["filename"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "append_to_file",
                    "description": "Append text to an existing file on the Desktop",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "filename": {"type": "string"},
                            "content":  {"type": "string"},
                        },
                        "required": ["filename", "content"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "delete_file",
                    "description": "Delete a file from the Desktop",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "filename": {"type": "string"}
                        },
                        "required": ["filename"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "list_desktop_files",
                    "description": "List all files currently on the Desktop",
                    "parameters": {"type": "object", "properties": {}, "required": []},
                },
            },
        ]

    def get_functions(self) -> Dict[str, Callable]:
        return {
            "create_file":       self.create_file,
            "read_file":         self.read_file,
            "append_to_file":    self.append_to_file,
            "delete_file":       self.delete_file,
            "list_desktop_files":self.list_desktop_files,
        }

    def _path(self, filename: str) -> str:
        # Prevent path traversal
        safe = os.path.basename(filename)
        return os.path.join(_DESKTOP, safe)

    def create_file(self, filename: str, content: str) -> str:
        try:
            path = self._path(filename)
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
            return json.dumps({"status": "success",
                               "message": f"File '{filename}' created on your Desktop."})
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})

    def read_file(self, filename: str) -> str:
        try:
            path = self._path(filename)
            if not os.path.exists(path):
                return json.dumps({"status": "error",
                                   "message": f"'{filename}' not found on Desktop."})
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            # Truncate very long files for voice
            if len(content) > 500:
                content = content[:500] + "... (truncated)"
            return json.dumps({"status": "success", "content": content})
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})

    def append_to_file(self, filename: str, content: str) -> str:
        try:
            path = self._path(filename)
            with open(path, "a", encoding="utf-8") as f:
                f.write("\n" + content)
            return json.dumps({"status": "success",
                               "message": f"Added text to '{filename}'."})
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})

    def delete_file(self, filename: str) -> str:
        try:
            path = self._path(filename)
            if not os.path.exists(path):
                return json.dumps({"status": "error",
                                   "message": f"'{filename}' not found on Desktop."})
            os.remove(path)
            return json.dumps({"status": "success",
                               "message": f"'{filename}' has been deleted."})
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})

    def list_desktop_files(self) -> str:
        try:
            files = [f for f in os.listdir(_DESKTOP)
                     if os.path.isfile(os.path.join(_DESKTOP, f))]
            if not files:
                return json.dumps({"status": "success",
                                   "message": "Your Desktop has no files."})
            names = ", ".join(files[:15])
            return json.dumps({"status": "success",
                               "message": f"Your Desktop has {len(files)} files: {names}."})
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})
