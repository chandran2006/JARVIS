import json
import webbrowser
import urllib.parse
import subprocess
import os
from typing import List, Dict, Any, Callable
from core.skill import Skill

BRAVE = r"C:\Users\ganes\AppData\Local\BraveSoftware\Brave-Browser\Application\brave.exe"

def _open_in_brave(url: str) -> bool:
    """Open URL in Brave. Falls back to default browser if Brave not found."""
    if os.path.exists(BRAVE):
        subprocess.Popen([BRAVE, url], creationflags=subprocess.CREATE_NO_WINDOW)
        return True
    webbrowser.open(url)
    return False


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
            _open_in_brave(urls.get(engine, urls["google"]))
            return json.dumps({"status": "success",
                               "message": f"Opened {engine} search for {query}."})
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})

    def open_website(self, url: str) -> str:
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
            _open_in_brave(url)
            return json.dumps({"status": "success",
                               "message": f"Opened {url} in Brave, sir."})
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
        import requests, xml.etree.ElementTree as ET

        # Free RSS feeds — no API key needed
        _RSS = {
            "general":     [
                "https://feeds.bbci.co.uk/news/rss.xml",
                "https://rss.cnn.com/rss/edition.rss",
                "https://feeds.reuters.com/reuters/topNews",
                "https://timesofindia.indiatimes.com/rssfeedstopstories.cms",
            ],
            "india":       [
                "https://timesofindia.indiatimes.com/rssfeedstopstories.cms",
                "https://www.thehindu.com/feeder/default.rss",
                "https://feeds.feedburner.com/ndtvnews-top-stories",
            ],
            "world":       [
                "https://feeds.bbci.co.uk/news/world/rss.xml",
                "https://rss.cnn.com/rss/edition_world.rss",
                "https://feeds.reuters.com/Reuters/worldNews",
                "https://feeds.skynews.com/feeds/rss/world.xml",
            ],
            "technology":  [
                "https://feeds.feedburner.com/TechCrunch",
                "https://www.wired.com/feed/rss",
                "https://feeds.arstechnica.com/arstechnica/index",
                "https://feeds.bbci.co.uk/news/technology/rss.xml",
            ],
            "business":    [
                "https://feeds.bbci.co.uk/news/business/rss.xml",
                "https://feeds.reuters.com/reuters/businessNews",
                "https://economictimes.indiatimes.com/rssfeedstopstories.cms",
            ],
            "sports":      [
                "https://feeds.bbci.co.uk/sport/rss.xml",
                "https://rss.cnn.com/rss/edition_sport.rss",
                "https://timesofindia.indiatimes.com/rssfeeds/4719148.cms",
            ],
            "science":     [
                "https://feeds.bbci.co.uk/news/science_and_environment/rss.xml",
                "https://www.sciencedaily.com/rss/top/science.xml",
                "https://feeds.reuters.com/reuters/scienceNews",
            ],
            "health":      [
                "https://feeds.bbci.co.uk/news/health/rss.xml",
                "https://feeds.reuters.com/reuters/healthNews",
                "https://www.who.int/rss-feeds/news-english.xml",
            ],
            "entertainment": [
                "https://feeds.bbci.co.uk/news/entertainment_and_arts/rss.xml",
                "https://rss.cnn.com/rss/edition_entertainment.rss",
            ],
            "politics":    [
                "https://feeds.bbci.co.uk/news/politics/rss.xml",
                "https://feeds.reuters.com/Reuters/PoliticsNews",
                "https://timesofindia.indiatimes.com/rssfeeds/1221656.cms",
            ],
        }

        cat = category.lower().strip()
        # fuzzy match category
        feeds = _RSS.get(cat)
        if not feeds:
            for key in _RSS:
                if key in cat or cat in key:
                    feeds = _RSS[key]
                    break
        if not feeds:
            feeds = _RSS["general"]

        headlines = []
        headers = {"User-Agent": "Mozilla/5.0"}
        for url in feeds:
            if len(headlines) >= 5:
                break
            try:
                r = requests.get(url, headers=headers, timeout=6)
                root = ET.fromstring(r.content)
                # Handle both RSS and Atom
                items = root.findall(".//item") or root.findall(
                    ".//{http://www.w3.org/2005/Atom}entry")
                for item in items[:3]:
                    title = (item.findtext("title") or
                             item.findtext("{http://www.w3.org/2005/Atom}title") or "").strip()
                    # Clean HTML entities
                    title = title.replace("&amp;", "&").replace("&lt;", "<").replace(
                        "&gt;", ">").replace("&quot;", '"').replace("&#39;", "'")
                    if title and title not in headlines:
                        headlines.append(title)
                    if len(headlines) >= 5:
                        break
            except Exception:
                continue

        if not headlines:
            webbrowser.open(f"https://news.google.com/search?q={urllib.parse.quote(category)}")
            return json.dumps({"status": "success",
                               "message": f"Opened Google News for {category}, sir."})

        msg = f"Top {cat} news. " + ". ".join(f"{i+1}. {h}" for i, h in enumerate(headlines)) + "."
        return json.dumps({"status": "success", "message": msg})

    def play_youtube(self, query: str) -> str:
        q = urllib.parse.quote_plus(query)
        try:
            # Try to get the first video URL directly so it auto-plays
            import requests
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
            r = requests.get(
                f"https://www.youtube.com/results?search_query={q}",
                headers=headers, timeout=6
            )
            # Extract first video ID from response
            import re
            match = re.search(r'"videoId":"([a-zA-Z0-9_-]{11})"', r.text)
            if match:
                video_url = f"https://www.youtube.com/watch?v={match.group(1)}&autoplay=1"
                _open_in_brave(video_url)
                return json.dumps({"status": "success",
                                   "message": f"Playing {query} on YouTube, sir."})
        except Exception:
            pass
        # Fallback: open search results
        _open_in_brave(f"https://www.youtube.com/results?search_query={q}")
        return json.dumps({"status": "success",
                           "message": f"Opening {query} on YouTube, sir."})
