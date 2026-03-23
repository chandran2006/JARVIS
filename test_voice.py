"""
Quick test for JARVIS voice functionality
"""

from core.voice import speak, listen

print("Testing JARVIS Voice System")
print("=" * 50)

# Test 1: Basic speech
print("\n1. Testing basic speech...")
speak("Hello, I am JARVIS. Voice system online.")

# Test 2: Time response (simulated)
print("\n2. Testing time response...")
import json
time_response = json.dumps({"status": "success", "time": "03:45 PM"})
speak(time_response)

# Test 3: Date response (simulated)
print("\n3. Testing date response...")
date_response = json.dumps({"status": "success", "date": "Monday, January 20, 2025"})
speak(date_response)

# Test 4: DateTime response (simulated)
print("\n4. Testing datetime response...")
datetime_response = json.dumps({"status": "success", "datetime": "Monday, January 20, 2025 at 03:45 PM"})
speak(datetime_response)

print("\n" + "=" * 50)
print("Voice test complete!")
print("\nNow try running JARVIS:")
print("  python main.py")
print("\nThen say:")
print('  "Jarvis, what time is it?"')
