import webbrowser
import json
from typing import List, Dict, Any, Callable
from core.skill import Skill

class WebSkill(Skill):
    @property
    def name(self) -> str:
        return "web_skill"

    def get_tools(self) -> List[Dict[str, Any]]:
        return [
            {
                "type": "function",
                "function": {
                    "name": "google_search",
                    "description": "Search Google for a query",
                    "parameters": { "type": "object", "properties": { "search_term": {"type": "string"} }, "required": ["search_term"] }
                }
            }
        ]

    def get_functions(self) -> Dict[str, Callable]:
        return {
            "google_search": self.google_search
        }

    def google_search(self, search_term):
        try:
            webbrowser.open(f"https://www.google.com/search?q={search_term}")
            return json.dumps({"status": "opened browser", "term": search_term})
        except Exception as e:
             return json.dumps({"error": str(e)})
