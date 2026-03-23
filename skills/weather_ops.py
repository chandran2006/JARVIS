import os
import json
from typing import List, Dict, Any, Callable
from core.skill import Skill

class WeatherSkill(Skill):
    """Skill for fetching weather information using OpenWeatherMap API."""
    
    def __init__(self):
        self.api_key = os.environ.get("OPENWEATHERMAP_API_KEY")
        self.default_city = os.environ.get("DEFAULT_CITY", "Mumbai")
    
    @property
    def name(self) -> str:
        return "weather_skill"

    def get_tools(self) -> List[Dict[str, Any]]:
        return [
            {
                "type": "function",
                "function": {
                    "name": "get_weather",
                    "description": "Get current weather information for a specified city or pincode",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "city": {
                                "type": "string",
                                "description": "Name of the city or pincode to get weather for"
                            },
                            "pincode": {
                                "type": "string",
                                "description": "Pincode of the location (optional). If provided, it takes precedence."
                            }
                        },
                        "required": ["city"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_current_location_weather",
                    "description": "Get current weather for the default/current location",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                }
            }
        ]

    def get_functions(self) -> Dict[str, Callable]:
        return {
            "get_weather": self.get_weather,
            "get_current_location_weather": self.get_current_location_weather
        }

    def get_weather(self, city: str, pincode: str = None) -> str:
        """
        Fetch weather data for a specific city or pincode.
        
        Args:
            city: Name of the city (or pincode if passed here)
            pincode: Optional pincode.
            
        Returns:
            JSON string with weather information
        """
        if not self.api_key:
            return json.dumps({
                "status": "error",
                "message": "OpenWeatherMap API key not configured. Please add OPENWEATHERMAP_API_KEY to .env file."
            })
        
        try:
            import requests
            
            url = f"http://api.openweathermap.org/data/2.5/weather"
            params = {
                "appid": self.api_key,
                "units": "metric"  # Celsius
            }

            # Check if input 'city' is actually a pincode (digits)
            is_numeric = city.strip().isdigit()
            
            if pincode:
                params["zip"] = f"{pincode},in" # Default to India
            elif is_numeric:
                 params["zip"] = f"{city},in" # Default to India
            else:
                params["q"] = city
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                weather_info = {
                    "status": "success",
                    "city": data["name"],
                    "location_id": data.get("id", "unknown"),
                    "country": data["sys"]["country"],
                    "coordinates": f"Lat: {data['coord']['lat']}, Lon: {data['coord']['lon']}",
                    "temperature": f"{data['main']['temp']:.1f}°C",
                    "feels_like": f"{data['main']['feels_like']:.1f}°C",
                    "conditions": data["weather"][0]["description"].title(),
                    "humidity": f"{data['main']['humidity']}%",
                    "wind_speed": f"{data['wind']['speed']} m/s"
                }

                # Try to extract pincode/zip if available implies we searched by it or it might not be directly in response standard fields easily without reverse geocoding, 
                # but we can return the confirmed location name.
                
                return json.dumps(weather_info)
            elif response.status_code == 404:
                return json.dumps({
                    "status": "error",
                    "message": f"Location '{pincode if pincode else city}' not found"
                })
            else:
                return json.dumps({
                    "status": "error",
                    "message": f"Weather API error: {response.status_code}"
                })
                
        except ImportError:
            return json.dumps({
                "status": "error",
                "message": "requests library not installed. Run: pip3 install requests"
            })
        except Exception as e:
            return json.dumps({
                "status": "error",
                "message": f"Weather fetch error: {str(e)}"
            })

    def get_current_location_weather(self) -> str:
        """Get weather for the default city configured in .env"""
        return self.get_weather(self.default_city)
