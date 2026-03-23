#!/usr/bin/env python3
"""
JARVIS Setup and Diagnostic Tool
Helps with installation, configuration, and troubleshooting
"""

import os
import sys
import platform
import subprocess
from pathlib import Path

class Colors:
    """ANSI color codes for terminal output."""
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'

def print_header(text):
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}{text.center(60)}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'='*60}{Colors.END}\n")

def print_success(text):
    print(f"{Colors.GREEN}✓ {text}{Colors.END}")

def print_error(text):
    print(f"{Colors.RED}✗ {text}{Colors.END}")

def print_warning(text):
    print(f"{Colors.YELLOW}⚠ {text}{Colors.END}")

def print_info(text):
    print(f"{Colors.BLUE}ℹ {text}{Colors.END}")

def check_python_version():
    """Check if Python version is compatible."""
    print_header("Checking Python Version")
    
    version = sys.version_info
    version_str = f"{version.major}.{version.minor}.{version.micro}"
    
    print(f"Python Version: {version_str}")
    print(f"Platform: {platform.system()} {platform.release()}")
    
    if version.major == 3 and version.minor >= 8:
        print_success("Python version is compatible")
        return True
    else:
        print_error("Python 3.8+ required")
        print_info("Download from: https://www.python.org/downloads/")
        return False

def check_dependencies():
    """Check if required packages are installed."""
    print_header("Checking Dependencies")
    
    required = {
        "groq": "Groq API client",
        "dotenv": "Environment variables (python-dotenv)",
        "PyQt6": "GUI framework",
        "pyttsx3": "Text-to-speech",
        "speech_recognition": "Speech recognition",
        "requests": "HTTP library",
        "psutil": "System monitoring"
    }
    
    missing = []
    
    for package, description in required.items():
        try:
            __import__(package)
            print_success(f"{package}: {description}")
        except ImportError:
            print_error(f"{package}: {description} - NOT INSTALLED")
            missing.append(package)
    
    if missing:
        print_warning(f"\nMissing {len(missing)} packages")
        print_info("Install with: pip install -r requirements_enhanced.txt")
        return False
    else:
        print_success("\nAll dependencies installed")
        return True

def check_api_keys():
    """Check if API keys are configured."""
    print_header("Checking API Keys")
    
    env_file = Path(".env")
    
    if not env_file.exists():
        print_error(".env file not found")
        print_info("Create .env file with: GROQ_API_KEY=your_key_here")
        return False
    
    from dotenv import load_dotenv
    load_dotenv()
    
    groq_key = os.getenv("GROQ_API_KEY")
    
    if groq_key:
        print_success(f"GROQ_API_KEY configured ({groq_key[:10]}...)")
        return True
    else:
        print_error("GROQ_API_KEY not found in .env")
        print_info("Get your key from: https://console.groq.com/")
        return False

def check_audio_support():
    """Check if audio devices are available."""
    print_header("Checking Audio Support")
    
    try:
        import pyaudio
        p = pyaudio.PyAudio()
        
        input_devices = 0
        output_devices = 0
        
        for i in range(p.get_device_count()):
            info = p.get_device_info_by_index(i)
            if info['maxInputChannels'] > 0:
                input_devices += 1
            if info['maxOutputChannels'] > 0:
                output_devices += 1
        
        p.terminate()
        
        print_success(f"Input devices: {input_devices}")
        print_success(f"Output devices: {output_devices}")
        
        if input_devices == 0:
            print_warning("No microphone detected - voice input unavailable")
        if output_devices == 0:
            print_warning("No speakers detected - voice output unavailable")
        
        return input_devices > 0 and output_devices > 0
        
    except ImportError:
        print_error("PyAudio not installed")
        print_info("Voice features will not work")
        return False
    except Exception as e:
        print_error(f"Audio check failed: {e}")
        return False

def test_groq_connection():
    """Test connection to Groq API."""
    print_header("Testing Groq API Connection")
    
    try:
        from groq import Groq
        from dotenv import load_dotenv
        
        load_dotenv()
        client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": "Say 'Connection successful' in 3 words"}],
            max_tokens=10
        )
        
        result = response.choices[0].message.content
        print_success(f"API Response: {result}")
        return True
        
    except Exception as e:
        print_error(f"Connection failed: {e}")
        print_info("Check your API key and internet connection")
        return False

def check_skills():
    """Check if skills are loadable."""
    print_header("Checking Skills")
    
    skills_dir = Path("skills")
    
    if not skills_dir.exists():
        print_error("Skills directory not found")
        return False
    
    skill_files = list(skills_dir.glob("*.py"))
    skill_files = [f for f in skill_files if not f.name.startswith("_")]
    
    print_info(f"Found {len(skill_files)} skill files")
    
    for skill_file in skill_files:
        print(f"  • {skill_file.name}")
    
    print_success("Skills directory OK")
    return True

def create_env_template():
    """Create .env template file."""
    print_header("Creating .env Template")
    
    template = """# JARVIS Environment Configuration
# Get your Groq API key from: https://console.groq.com/

GROQ_API_KEY=your_groq_api_key_here

# Optional: Gemini API for advanced vision features
# GEMINI_API_KEY=your_gemini_api_key_here

# Optional: Custom settings
# JARVIS_THEME=STARK
# JARVIS_VOICE_RATE=175
"""
    
    env_file = Path(".env")
    
    if env_file.exists():
        print_warning(".env file already exists")
        response = input("Overwrite? (y/N): ")
        if response.lower() != 'y':
            print_info("Skipped")
            return
    
    with open(env_file, 'w') as f:
        f.write(template)
    
    print_success(".env template created")
    print_info("Edit .env and add your API keys")

def run_diagnostics():
    """Run all diagnostic checks."""
    print(f"\n{Colors.BOLD}{Colors.HEADER}")
    print("╔═══════════════════════════════════════════════════════════╗")
    print("║         JARVIS Setup & Diagnostic Tool                   ║")
    print("╚═══════════════════════════════════════════════════════════╝")
    print(f"{Colors.END}")
    
    results = {
        "Python Version": check_python_version(),
        "Dependencies": check_dependencies(),
        "API Keys": check_api_keys(),
        "Audio Support": check_audio_support(),
        "Groq Connection": test_groq_connection(),
        "Skills": check_skills()
    }
    
    print_header("Diagnostic Summary")
    
    passed = sum(results.values())
    total = len(results)
    
    for check, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        color = Colors.GREEN if result else Colors.RED
        print(f"{color}{status}{Colors.END} - {check}")
    
    print(f"\n{Colors.BOLD}Score: {passed}/{total}{Colors.END}")
    
    if passed == total:
        print_success("\n🎉 All checks passed! JARVIS is ready to run.")
        print_info("Start with: python main_enhanced.py")
    else:
        print_warning(f"\n⚠️  {total - passed} checks failed")
        print_info("Fix the issues above before running JARVIS")

def show_menu():
    """Show interactive menu."""
    while True:
        print(f"\n{Colors.BOLD}{Colors.CYAN}JARVIS Setup Menu{Colors.END}")
        print("1. Run full diagnostics")
        print("2. Check dependencies only")
        print("3. Test Groq API connection")
        print("4. Create .env template")
        print("5. Check audio devices")
        print("6. Exit")
        
        choice = input(f"\n{Colors.BOLD}Select option (1-6): {Colors.END}")
        
        if choice == "1":
            run_diagnostics()
        elif choice == "2":
            check_dependencies()
        elif choice == "3":
            test_groq_connection()
        elif choice == "4":
            create_env_template()
        elif choice == "5":
            check_audio_support()
        elif choice == "6":
            print_info("Goodbye!")
            break
        else:
            print_error("Invalid option")

def main():
    """Main entry point."""
    if len(sys.argv) > 1:
        if sys.argv[1] == "--full":
            run_diagnostics()
        elif sys.argv[1] == "--deps":
            check_dependencies()
        elif sys.argv[1] == "--api":
            test_groq_connection()
        elif sys.argv[1] == "--env":
            create_env_template()
        else:
            print("Usage: python setup_helper.py [--full|--deps|--api|--env]")
    else:
        show_menu()

if __name__ == "__main__":
    main()
