import os
import sys
from dotenv import load_dotenv
from groq import Groq

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Load environment variables
load_dotenv()

# Get API key
api_key = os.environ.get("GROQ_API_KEY")

if not api_key:
    print("[ERROR] GROQ_API_KEY not found in .env file")
    exit(1)

print("[OK] API Key loaded successfully")
print(f"     Key preview: {api_key[:10]}...{api_key[-10:]}")

# Initialize Groq client
try:
    client = Groq(api_key=api_key)
    print("[OK] Groq client initialized")
except Exception as e:
    print(f"[ERROR] Failed to initialize Groq client: {e}")
    exit(1)

# Test connection with a simple chat completion
try:
    print("\n[TEST] Testing chat completion...")
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": "You are Jarvis, Tony Stark's AI assistant."},
            {"role": "user", "content": "Hello Jarvis, introduce yourself briefly."}
        ],
        max_tokens=100
    )
    
    print("[OK] Connection successful!\n")
    print("=" * 50)
    print("JARVIS Response:")
    print("=" * 50)
    print(response.choices[0].message.content)
    print("=" * 50)
    
except Exception as e:
    print(f"[ERROR] API call failed: {e}")
    exit(1)

print("\n[SUCCESS] All tests passed! Your Groq API is ready to use.")
