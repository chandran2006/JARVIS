import os
from dotenv import load_dotenv
from google import genai

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    print("Error: GEMINI_API_KEY not found.")
    exit(1)

client = genai.Client(api_key=api_key, http_options={'api_version': 'v1alpha'})

print("Listing models...")
try:
    # List all models
    # The SDK might have a different method for listing, usually client.models.list()
    # But specifically checking for Realtime/Bidi support is key.
    # We will list all and print their names.
    for model in client.models.list():
        print(f"Model: {model.name}")
        # print(f"  Supported: {model.supported_generation_methods}")
except Exception as e:
    print(f"Error listing models: {e}")

print("\nTrying to connect to specific models for Bidi (Live)...")
models_to_test = ["gemini-2.0-flash-exp", "gemini-1.5-pro", "gemini-1.5-flash"]
pass
