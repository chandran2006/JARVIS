import os
import json
from datetime import datetime
from typing import List, Dict, Any, Callable
from core.skill import Skill

_NOTES_DIR = os.path.join(os.path.expanduser("~"), "Desktop", "JARVIS_Notes")

class NotesSkill(Skill):
    def __init__(self):
        os.makedirs(_NOTES_DIR, exist_ok=True)

    @property
    def name(self) -> str:
        return "notes_skill"

    def get_tools(self) -> List[Dict[str, Any]]:
        return [
            {"type":"function","function":{"name":"create_note",
             "description":"Create a quick note with a title and content",
             "parameters":{"type":"object","properties":{
                 "title":  {"type":"string","description":"Short title for the note"},
                 "content":{"type":"string","description":"The note content"}},
             "required":["title","content"]}}},
            {"type":"function","function":{"name":"read_note",
             "description":"Read a saved note by title",
             "parameters":{"type":"object","properties":{
                 "title":{"type":"string"}},"required":["title"]}}},
            {"type":"function","function":{"name":"list_notes",
             "description":"List all saved notes",
             "parameters":{"type":"object","properties":{},"required":[]}}},
            {"type":"function","function":{"name":"delete_note",
             "description":"Delete a note by title",
             "parameters":{"type":"object","properties":{
                 "title":{"type":"string"}},"required":["title"]}}},
        ]

    def get_functions(self) -> Dict[str, Callable]:
        return {
            "create_note": self.create_note,
            "read_note":   self.read_note,
            "list_notes":  self.list_notes,
            "delete_note": self.delete_note,
        }

    def _path(self, title: str) -> str:
        safe = "".join(c for c in title if c.isalnum() or c in " _-").strip()
        return os.path.join(_NOTES_DIR, safe + ".txt")

    def create_note(self, title: str, content: str) -> str:
        try:
            with open(self._path(title), "w", encoding="utf-8") as f:
                f.write(f"Title: {title}\n")
                f.write(f"Created: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
                f.write("-" * 40 + "\n")
                f.write(content)
            return json.dumps({"status":"success",
                               "message":f"Note '{title}' saved to your Desktop in the JARVIS Notes folder."})
        except Exception as e:
            return json.dumps({"status":"error","message":str(e)})

    def read_note(self, title: str) -> str:
        try:
            p = self._path(title)
            if not os.path.exists(p):
                return json.dumps({"status":"error","message":f"I could not find a note called '{title}'."})
            with open(p, "r", encoding="utf-8") as f:
                content = f.read()
            short = content[:400] + ("..." if len(content) > 400 else "")
            return json.dumps({"status":"success","message":short})
        except Exception as e:
            return json.dumps({"status":"error","message":str(e)})

    def list_notes(self) -> str:
        try:
            notes = [f[:-4] for f in os.listdir(_NOTES_DIR) if f.endswith(".txt")]
            if not notes:
                return json.dumps({"status":"success","message":"You have no saved notes yet, sir."})
            return json.dumps({"status":"success",
                               "message":f"You have {len(notes)} notes: {', '.join(notes)}."})
        except Exception as e:
            return json.dumps({"status":"error","message":str(e)})

    def delete_note(self, title: str) -> str:
        try:
            p = self._path(title)
            if not os.path.exists(p):
                return json.dumps({"status":"error","message":f"No note called '{title}' found."})
            os.remove(p)
            return json.dumps({"status":"success","message":f"Note '{title}' deleted."})
        except Exception as e:
            return json.dumps({"status":"error","message":str(e)})
