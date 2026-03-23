import os
import sys
import argparse
import threading 
import time
from dotenv import load_dotenv
from core.voice import speak, listen
from core.registry import SkillRegistry
from core.engine import JarvisEngine
from gui.app import run_gui as run_gui_app

# Load Env
load_dotenv()

if not os.environ.get("GROQ_API_KEY"):
    print("Error: GROQ_API_KEY not found.")
    sys.exit(1)

def jarvis_loop(pause_event, registry, args):
    """
    Main loop for JARVIS, running in a separate thread.
    Checks pause_event to determine if it should listen/process.
    """
    # Initialize Engine
    jarvis = JarvisEngine(registry)

    if args.text:
        print("JARVIS: Jarvis Online. Ready for command (Text Mode).")
    else:
        speak("Jarvis Online. Ready for command.")

    while True:
        # Check for pause
        if pause_event.is_set():
            time.sleep(0.5)
            continue

        if args.text:
            try:
                user_query = input("YOU: ").lower()
            except EOFError:
                break
        else:
            user_query = listen()
            
        # Double check pause after listening (in case paused during listen)
        if pause_event.is_set():
            continue

        if user_query == "none" or not user_query: continue
        if "quit" in user_query: 
            print("Shutting down JARVIS loop...")
            # We can't easily kill the main thread (GUI) from here, 
            # but we can stop this loop. The user will have to close the GUI.
            speak("Shutting down.")
            break
        
        # Wake word / Command filtering Logic
        direct_commands = [
            "open", "volume", "search", "create", "write", "read", "make",
            "who", "what", "when", "where", "how", "why", "thank", "hello"
        ]
        
        is_direct = any(cmd in user_query for cmd in direct_commands)
        
        if "jarvis" not in user_query and not is_direct:
            print(f"Ignored: {user_query}")
            continue
            
        clean_query = user_query.replace("jarvis", "").strip()
        
        try:
            print(f"Thinking: {clean_query}")
            response = jarvis.run_conversation(clean_query)
            
            # Check pause before speaking response
            if pause_event.is_set():
                continue

            if response:
                if args.text:
                    print(f"JARVIS: {response}")
                else:
                    speak(response)
        except Exception as e:
            print(f"Main Loop Error: {e}")
            if args.text:
                print("JARVIS: System error.")
            else:
                speak("System error.")

def main():
    parser = argparse.ArgumentParser(description="JARVIS AI Assistant")
    parser.add_argument("--text", action="store_true", help="Run in text mode (no voice I/O)")
    args = parser.parse_args()

    # 1. Initialize Registry and Load Skills
    registry = SkillRegistry()
    skills_dir = os.path.join(os.path.dirname(__file__), "skills")
    registry.load_skills(skills_dir)
    
    # 2. Setup Pause Event
    # Event is SET when PAUSED, CLEARED when RUNNING
    pause_event = threading.Event()
    
    # 3. Start JARVIS Loop in Background Thread
    # Daemon thread so it dies when GUI closes
    t = threading.Thread(target=jarvis_loop, args=(pause_event, registry, args), daemon=True)
    t.start()
    
    # 4. Start GUI in Main Thread (Required for PyQt)
    # This will block until the window is closed
    run_gui_app(pause_event)

if __name__ == "__main__":
    main()