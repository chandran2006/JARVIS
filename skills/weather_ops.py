import os
import json
import webbrowser
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
                "description": "Get current weather, temperature, humidity, wind for any city",
                "parameters": {"type": "object",
                               "properties": {"city": {"type": "string"}},
                               "required": ["city"]}}},
            {"type": "function", "function": {
                "name": "get_local_weather",
                "description": "Get weather for the default home city",
                "parameters": {"type": "object", "properties": {}, "required": []}}},
            {"type": "function", "function": {
                "name": "get_weather_forecast",
                "description": "Get 3-day weather forecast for any city",
                "parameters": {"type": "object",
                               "properties": {"city": {"type": "string"}},
                               "required": ["city"]}}},
        ]

    def get_functions(self) -> Dict[str, Callable]:
        return {
            "get_weather":          self.get_weather,
            "get_local_weather":    self.get_local_weather,
            "get_weather_forecast": self.get_weather_forecast,
        }

    def get_weather(self, city: str) -> str:
        if self.api_key:
            result = self._owm_weather(city)
            if result:
                return result
        return self._wttr_weather(city)

    def _owm_weather(self, city: str):
        try:
            import requests
            r = requests.get(
                "http://api.openweathermap.org/data/2.5/weather",
                params={"q": city, "appid": self.api_key, "units": "metric"},
                timeout=4)
            if r.status_code != 200:
                return None
            d = r.json()
            msg = (
                f"In {d['name']} it is {d['main']['temp']:.0f} degrees Celsius, "
                f"feels like {d['main']['feels_like']:.0f} degrees, "
                f"{d['weather'][0]['description']}, "
                f"humidity is {d['main']['humidity']} percent, "
                f"and wind speed is {d['wind']['speed']} metres per second."
            )
            return json.dumps({"status": "success", "message": msg})
        except Exception:
            return None

    def _wttr_weather(self, city: str) -> str:
        try:
            import requests
            r = requests.get(
                f"https://wttr.in/{city.replace(' ', '+')}",
                params={"format": "j1"},
                timeout=4,
                headers={"User-Agent": "JARVIS/1.0"})
            if r.status_code != 200:
                raise Exception(f"HTTP {r.status_code}")
            d       = r.json()
            cur     = d["current_condition"][0]
            area    = d["nearest_area"][0]
            name    = area["areaName"][0]["value"]
            country = area["country"][0]["value"]
            msg = (
                f"In {name}, {country} it is {cur['temp_C']} degrees Celsius, "
                f"feels like {cur['FeelsLikeC']} degrees, "
                f"{cur['weatherDesc'][0]['value'].lower()}, "
                f"humidity is {cur['humidity']} percent, "
                f"and wind speed is {cur['windspeedKmph']} kilometres per hour."
            )
            return json.dumps({"status": "success", "message": msg})
        except Exception:
            webbrowser.open(f"https://www.google.com/search?q=weather+in+{city.replace(' ', '+')}")
            return json.dumps({"status": "success",
                               "message": f"Opened Google weather for {city} in your browser, sir."})

    def get_local_weather(self) -> str:
        return self.get_weather(self.default_city)

    def get_weather_forecast(self, city: str) -> str:
        try:
            import requests
            r = requests.get(
                f"https://wttr.in/{city.replace(' ', '+')}",
                params={"format": "j1"},
                timeout=4,
                headers={"User-Agent": "JARVIS/1.0"})
            if r.status_code != 200:
                raise Exception(f"HTTP {r.status_code}")
            days  = r.json().get("weather", [])[:3]
            parts = []
            for day in days:
                desc = day["hourly"][4]["weatherDesc"][0]["value"]
                parts.append(f"{day['date']}: {desc.lower()}, high {day['maxtempC']}, low {day['mintempC']} degrees")
            msg = f"3-day forecast for {city}: " + "; ".join(parts) + "."
            return json.dumps({"status": "success", "message": msg})
        except Exception:
            webbrowser.open(f"https://www.google.com/search?q=weather+forecast+{city.replace(' ', '+')}")
            return json.dumps({"status": "success",
                               "message": f"Opened Google forecast for {city} in your browser, sir."})
