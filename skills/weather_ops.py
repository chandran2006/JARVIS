import os
import json
from typing import List, Dict, Any, Callable
from core.skill import Skill

class WeatherSkill(Skill):
    def __init__(self):
        self.api_key      = os.environ.get("OPENWEATHERMAP_API_KEY", "")
        self.default_city = os.environ.get("DEFAULT_CITY", "Chennai")

    @property
    def name(self) -> str:
        return "weather_skill"

    def get_tools(self) -> List[Dict[str, Any]]:
        return [
            {"type": "function", "function": {
                "name": "get_weather",
                "description": "Get current weather for any city",
                "parameters": {"type": "object",
                               "properties": {"city": {"type": "string"}},
                               "required": ["city"]}}},
            {"type": "function", "function": {
                "name": "get_local_weather",
                "description": "Get weather for the default home city",
                "parameters": {"type": "object", "properties": {}, "required": []}}},
        ]

    def get_functions(self) -> Dict[str, Callable]:
        return {
            "get_weather":       self.get_weather,
            "get_local_weather": self.get_local_weather,
        }

    def get_weather(self, city: str) -> str:
        if not self.api_key:
            return json.dumps({"status": "error",
                               "message": "Weather API key not configured. "
                                          "Add OPENWEATHERMAP_API_KEY to your .env file."})
        try:
            import requests
            r = requests.get(
                "http://api.openweathermap.org/data/2.5/weather",
                params={"q": city, "appid": self.api_key, "units": "metric"},
                timeout=8)
            if r.status_code == 404:
                return json.dumps({"status": "error",
                                   "message": f"I could not find weather data for {city}."})
            r.raise_for_status()
            d = r.json()
            msg = (f"In {d['name']} it is {d['main']['temp']:.0f} degrees Celsius, "
                   f"feels like {d['main']['feels_like']:.0f}, "
                   f"{d['weather'][0]['description']}, "
                   f"humidity {d['main']['humidity']} percent, "
                   f"wind speed {d['wind']['speed']} metres per second.")
            return json.dumps({"status": "success", "message": msg})
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})

    def get_local_weather(self) -> str:
        return self.get_weather(self.default_city)
