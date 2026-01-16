import os
from google import genai
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
if not api_key:
    print("No API key found.")
    exit()

client = genai.Client(api_key=api_key)

print("Listing available models...")
try:
    for m in client.models.list():
        print(f"- {m.name} (Display: {m.display_name})")
except Exception as e:
    print(f"Error listing models: {e}")
