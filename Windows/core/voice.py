import os
import sys
import pyttsx3
import speech_recognition as sr

# Initialize engine globally to avoid re-initialization issues
engine = pyttsx3.init()

# Set voice to deep male voice
def set_deep_male_voice():
    voices = engine.getProperty('voices')
    for voice in voices:
        # Prefer "Daniel" for deep male voice on Mac
        if "Daniel" in voice.name:
            engine.setProperty('voice', voice.id)
            return
    # Fallback to any male voice if Daniel not found
    for voice in voices:
        if "male" in voice.name.lower() or "male" in str(voice.gender).lower():
             engine.setProperty('voice', voice.id)
             return

set_deep_male_voice()

def speak(text):
    if "{" in text and "}" in text and "status" in text:
        text = "Task completed."
    
    # Print first so user sees it even if audio fails
    print(f"JARVIS: {text}")

    # Use pyttsx3 for Windows (SAPI5)
    try:
        engine.say(text)
        engine.runAndWait()
    except Exception as e:
        print(f"TTS Error: {e}")

def listen():
    r = sr.Recognizer()
    with sr.Microphone() as source:
        print("Listening...")
        r.pause_threshold = 0.8
        r.adjust_for_ambient_noise(source)
        try:
            audio = r.listen(source, timeout=5)
            print("Recognizing...")
            query = r.recognize_google(audio)
            return query.lower()
        except Exception:
            return "none"
