from core.voice import speak, set_deep_male_voice
from skills.weather_ops import WeatherSkill
import json
import os
from dotenv import load_dotenv

load_dotenv()

# Test Voice
print("Testing Voice...")
set_deep_male_voice()
speak("This is a test of the deep male voice. I am JARVIS.")

# Test Weather
print("\nTesting Weather...")
weather_skill = WeatherSkill()

# Test Default (Mumbai)
print("Fetching default weather (Mumbai)...")
default_weather = weather_skill.get_current_location_weather()
print(f"Default Weather: {default_weather}")

# Test Pincode
pincode = "400001"
print(f"Fetching weather for pincode {pincode}...")
pincode_weather = weather_skill.get_weather(pincode)
print(f"Pincode Weather: {pincode_weather}")
