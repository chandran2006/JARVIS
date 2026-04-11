import json
import webbrowser
import urllib.parse
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
                "description": "Search Google, YouTube, GitHub, Wikipedia, or Reddit",
                "parameters": {"type": "object",
                               "properties": {
                                   "query":  {"type": "string"},
                                   "engine": {"type": "string",
                                              "enum": ["google", "youtube", "github", "wikipedia", "reddit", "bing"],
                                              "default": "google"}},
                               "required": ["query"]}}},
            {"type": "function", "function": {
                "name": "open_website",
                "description": "Open any URL or website name in the browser",
                "parameters": {"type": "object",
                               "properties": {"url": {"type": "string"}},
                               "required": ["url"]}}},
            {"type": "function", "function": {
                "name": "get_wikipedia_summary",
                "description": "Get a short Wikipedia summary for any topic",
                "parameters": {"type": "object",
                               "properties": {"topic": {"type": "string"}},
                               "required": ["topic"]}}},
            {"type": "function", "function": {
                "name": "get_top_news",
                "description": "Get top news headlines",
                "parameters": {"type": "object",
                               "properties": {"category": {"type": "string",
                                                           "enum": ["general", "technology", "sports", "business", "science"],
                                                           "default": "general"}},
                               "required": []}}},
            {"type": "function", "function": {
                "name": "play_youtube",
                "description": "Search and open a YouTube video",
                "parameters": {"type": "object",
                               "properties": {"query": {"type": "string"}},
                               "required": ["query"]}}},
        ]

    def get_functions(self) -> Dict[str, Callable]:
        return {
            "search_web":            self.search_web,
            "open_website":          self.open_website,
            "get_wikipedia_summary": self.get_wikipedia_summary,
            "get_top_news":          self.get_top_news,
            "play_youtube":          self.play_youtube,
        }

    def search_web(self, query: str, engine: str = "google") -> str:
        q = urllib.parse.quote_plus(query)
        urls = {
            "google":    f"https://www.google.com/search?q={q}",
            "youtube":   f"https://www.youtube.com/results?search_query={q}",
            "github":    f"https://github.com/search?q={q}",
            "wikipedia": f"https://en.wikipedia.org/wiki/Special:Search?search={q}",
            "reddit":    f"https://www.reddit.com/search/?q={q}",
            "bing":      f"https://www.bing.com/search?q={q}",
        }
        try:
            webbrowser.open(urls.get(engine, urls["google"]))
            return json.dumps({"status": "success",
                               "message": f"Opened {engine} search for {query}."})
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})

    def open_website(self, url: str) -> str:
        # Handle common site names without TLD
        shortcuts = {
            "youtube": "https://www.youtube.com",
            "google":  "https://www.google.com",
            "github":  "https://www.github.com",
            "reddit":  "https://www.reddit.com",
            "twitter": "https://www.twitter.com",
            "x":       "https://www.x.com",
            "facebook":"https://www.facebook.com",
            "instagram":"https://www.instagram.com",
            "linkedin":"https://www.linkedin.com",
            "netflix": "https://www.netflix.com",
            "amazon":  "https://www.amazon.in",
            "flipkart":"https://www.flipkart.com",
            "gmail":   "https://mail.google.com",
            "maps":    "https://maps.google.com",
            "drive":   "https://drive.google.com",
            "whatsapp":"https://web.whatsapp.com",
            "chatgpt": "https://chat.openai.com",
        }
        clean = url.lower().strip().rstrip("/")
        if clean in shortcuts:
            url = shortcuts[clean]
        elif not url.startswith(("http://", "https://")):
            url = "https://" + url
        try:
            webbrowser.open(url)
            return json.dumps({"status": "success",
                               "message": f"Opened {url} in your browser, sir."})
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})

    def get_wikipedia_summary(self, topic: str) -> str:
        try:
            import requests
            r = requests.get(
                "https://en.wikipedia.org/api/rest_v1/page/summary/"
                + urllib.parse.quote(topic.replace(" ", "_")),
                timeout=8)
            if r.status_code == 200:
                extract = r.json().get("extract", "")
                summary = ". ".join(extract.split(". ")[:2]) + "."
                return json.dumps({"status": "success", "message": summary})
            return json.dumps({"status": "error",
                               "message": f"I could not find a Wikipedia article on {topic}."})
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})

    def get_top_news(self, category: str = "general") -> str:
        try:
            import requests, os
            api_key = os.environ.get("NEWS_API_KEY", "")
            if not api_key:
                # Fallback: open Google News
                webbrowser.open(f"https://news.google.com/search?q={category}")
                return json.dumps({"status": "success",
                                   "message": f"Opened Google News for {category} headlines, sir."})
            r = requests.get(
                "https://newsapi.org/v2/top-headlines",
                params={"category": category, "country": "in", "pageSize": 5, "apiKey": api_key},
                timeout=8)
            articles = r.json().get("articles", [])
            if not articles:
                return json.dumps({"status": "success", "message": "No headlines found right now."})
            headlines = "; ".join(a["title"] for a in articles[:4])
            return json.dumps({"status": "success",
                               "message": f"Top {category} headlines: {headlines}."})
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})

    def play_youtube(self, query: str) -> str:
        q = urllib.parse.quote_plus(query)
        try:
            webbrowser.open(f"https://www.youtube.com/results?search_query={q}")
            return json.dumps({"status": "success",
                               "message": f"Searching YouTube for {query}, sir."})
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})
