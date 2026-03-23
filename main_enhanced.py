import os
import sys
import argparse
import threading
import time
from dotenv import load_dotenv
from core.voice import speak, listen
from core.enhanced_registry import EnhancedSkillRegistry
from core.enhanced_engine import EnhancedJarvisEngine
from gui.enhanced_app import run_enhanced_gui

# Load environment variables
load_dotenv()

if not os.environ.get("GROQ_API_KEY"):
    print("❌ Error: GROQ_API_KEY not found in environment.")
    print("💡 Create a .env file with: GROQ_API_KEY=your_key_here")
    sys.exit(1)

class JarvisController:
    """Main controller for JARVIS with enhanced features."""
    
    def __init__(self, args, pause_event):
        self.args = args
        self.pause_event = pause_event
        self.registry = EnhancedSkillRegistry()
        self.engine = None
        self.running = True
    
    def initialize(self):
        """Initialize JARVIS system."""
        
        print("🤖 JARVIS Advanced AI Assistant")
        print("=" * 50)
        
        # Load skills
        skills_dir = os.path.join(os.path.dirname(__file__), "skills")
        context = {"pause_event": self.pause_event}
        
        print("\n📦 Loading Skills...")
        self.registry.load_skills(skills_dir, context=context)
        
        # Initialize engine
        print("\n🧠 Initializing AI Engine...")
        self.engine = EnhancedJarvisEngine(self.registry)
        
        # Show stats
        stats = self.registry.get_skill_stats()
        print(f"\n✅ System Ready!")
        print(f"   • Skills: {stats['enabled_skills']}/{stats['total_skills']}")
        print(f"   • Tools: {stats['total_tools']}")
        print(f"   • Mode: {'TEXT' if self.args.text else 'VOICE'}")
        print("=" * 50)
    
    def run_loop(self):
        """Main JARVIS loop."""
        
        if not self.args.text:
            speak("JARVIS online. All systems operational.")
        else:
            print("\n💬 JARVIS: Online. Ready for commands (Text Mode).")
        
        while self.running:
            # Check pause state
            if self.pause_event.is_set():
                time.sleep(0.5)
                continue
            
            # Get user input
            if self.args.text:
                try:
                    user_query = input("\n👤 YOU: ").strip()
                except (EOFError, KeyboardInterrupt):
                    break
            else:
                user_query = listen()
            
            # Check pause again after listening
            if self.pause_event.is_set():
                continue
            
            if not user_query or user_query == "none":
                continue
            
            # Handle exit commands
            if any(cmd in user_query.lower() for cmd in ["quit", "exit", "shutdown"]):
                self.shutdown()
                break
            
            # Handle special commands
            if self.handle_special_commands(user_query):
                continue
            
            # Process with AI
            self.process_query(user_query)
    
    def handle_special_commands(self, query: str) -> bool:
        """Handle special system commands."""
        
        query_lower = query.lower()
        
        # Clear history
        if "clear history" in query_lower or "forget everything" in query_lower:
            self.engine.clear_history()
            response = "Memory cleared. Starting fresh."
            self.respond(response)
            return True
        
        # Show stats
        if "show stats" in query_lower or "system status" in query_lower:
            stats = self.registry.get_skill_stats()
            context = self.engine.get_context()
            
            response = (
                f"System Status:\n"
                f"Skills: {stats['enabled_skills']} active\n"
                f"Conversation: {context['history_length']} messages\n"
                f"Cache: {context['cache_size']} entries"
            )
            self.respond(response)
            return True
        
        # Reload skills
        if "reload skills" in query_lower:
            updated = self.registry.check_for_updates()
            if updated:
                for skill in updated:
                    self.registry.reload_skill(skill)
                response = f"Reloaded {len(updated)} skills."
            else:
                response = "All skills are up to date."
            self.respond(response)
            return True
        
        return False
    
    def process_query(self, query: str):
        """Process user query with AI engine."""
        
        # Wake word filtering
        wake_words = ["jarvis", "hey jarvis", "ok jarvis"]
        direct_commands = ["open", "search", "create", "set", "get", "show", "tell"]
        
        query_lower = query.lower()
        has_wake_word = any(wake in query_lower for wake in wake_words)
        has_direct_command = any(cmd in query_lower for cmd in direct_commands)
        
        if not has_wake_word and not has_direct_command:
            print(f"⏭️  Ignored: {query}")
            return
        
        # Remove wake word
        clean_query = query_lower
        for wake in wake_words:
            clean_query = clean_query.replace(wake, "").strip()
        
        if not clean_query:
            return
        
        try:
            print(f"\n💭 Processing: {clean_query}")
            response = self.engine.run_conversation(clean_query)
            
            if self.pause_event.is_set():
                return
            
            if response:
                self.respond(response)
        
        except Exception as e:
            error_msg = f"System error: {str(e)[:100]}"
            print(f"❌ {error_msg}")
            self.respond("I encountered an error processing that request.")
    
    def respond(self, text: str):
        """Send response to user."""
        
        if self.args.text:
            print(f"\n🤖 JARVIS: {text}")
        else:
            speak(text)
    
    def shutdown(self):
        """Gracefully shutdown JARVIS."""
        
        print("\n🔴 Shutting down JARVIS...")
        self.running = False
        
        if not self.args.text:
            speak("Shutting down. Goodbye, sir.")
        
        # Show final stats
        stats = self.registry.get_skill_stats()
        print("\n📊 Session Statistics:")
        for skill_name, skill_stats in stats["skills"].items():
            if skill_stats["calls"] > 0:
                print(f"   • {skill_name}: {skill_stats['calls']} calls")
        
        print("\n👋 JARVIS offline.")

def main():
    """Main entry point."""
    
    parser = argparse.ArgumentParser(
        description="JARVIS - Advanced AI Assistant",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main_enhanced.py              # Run with voice and GUI
  python main_enhanced.py --text       # Run in text-only mode
  python main_enhanced.py --no-gui     # Run voice without GUI
  python main_enhanced.py --theme ULTRON  # Use different theme
        """
    )
    
    parser.add_argument("--text", action="store_true", 
                       help="Run in text mode (no voice I/O)")
    parser.add_argument("--no-gui", action="store_true",
                       help="Run without GUI")
    parser.add_argument("--theme", choices=["STARK", "ULTRON", "VISION"],
                       default="STARK", help="GUI theme")
    
    args = parser.parse_args()
    
    # Create pause event
    pause_event = threading.Event()
    
    # Initialize controller
    controller = JarvisController(args, pause_event)
    controller.initialize()
    
    # Start JARVIS loop in background thread
    jarvis_thread = threading.Thread(
        target=controller.run_loop,
        daemon=True
    )
    jarvis_thread.start()
    
    # Start GUI if not disabled
    if not args.no_gui and not args.text:
        try:
            run_enhanced_gui(pause_event, args.theme)
        except KeyboardInterrupt:
            pass
    else:
        # Keep main thread alive
        try:
            jarvis_thread.join()
        except KeyboardInterrupt:
            controller.shutdown()

if __name__ == "__main__":
    main()
