import json
import webbrowser
from typing import List, Dict, Any, Callable
from core.skill import Skill

class WebSkill(Skill):
    @property
    def name(self) -> str:
        return "web_skill"

    def get_tools(self) -> List[Dict[str, Any]]:
        return [
            {"type": "function", "function": {
                "name": "search_web",
                "description": "Search Google, YouTube, GitHub, or Wikipedia",
                "parameters": {"type": "object",
                               "properties": {
                                   "query":  {"type": "string"},
                                   "engine": {"type": "string",
                                              "enum": ["google","youtube","github","wikipedia"],
                                              "default": "google"}},
                               "required": ["query"]}}},
            {"type": "function", "function": {
                "name": "open_website",
                "description": "Open any URL in the browser",
                "parameters": {"type": "object",
                               "properties": {"url": {"type": "string"}},
                               "required": ["url"]}}},
            {"type": "function", "function": {
                "name": "get_wikipedia_summary",
                "description": "Get a short Wikipedia summary for any topic",
                "parameters": {"type": "object",
                               "properties": {"topic": {"type": "string"}},
                               "required": ["topic"]}}},
        ]

    def get_functions(self) -> Dict[str, Callable]:
        return {
            "search_web":            self.search_web,
            "open_website":          self.open_website,
            "get_wikipedia_summary": self.get_wikipedia_summary,
        }

    def search_web(self, query: str, engine: str = "google") -> str:
        urls = {
            "google":    f"https://www.google.com/search?q={query}",
            "youtube":   f"https://www.youtube.com/results?search_query={query}",
            "github":    f"https://github.com/search?q={query}",
            "wikipedia": f"https://en.wikipedia.org/wiki/Special:Search?search={query}",
        }
        try:
            webbrowser.open(urls.get(engine, urls["google"]))
            return json.dumps({"status": "success",
                               "message": f"Opened {engine} search for {query}."})
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})

    def open_website(self, url: str) -> str:
        if not url.startswith(("http://", "https://")):
            url = "https://" + url
        try:
            webbrowser.open(url)
            return json.dumps({"status": "success",
                               "message": f"Opened {url} in your browser."})
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})

    def get_wikipedia_summary(self, topic: str) -> str:
        try:
            import requests
            r = requests.get(
                "https://en.wikipedia.org/api/rest_v1/page/summary/"
                + topic.replace(" ", "_"),
                timeout=8)
            if r.status_code == 200:
                extract = r.json().get("extract", "")
                summary = ". ".join(extract.split(". ")[:2]) + "."
                return json.dumps({"status": "success",
                                   "message": summary})
            return json.dumps({"status": "error",
                               "message": f"I could not find a Wikipedia article on {topic}."})
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})
