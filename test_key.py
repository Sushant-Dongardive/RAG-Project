import sys
import os

# Add the backend folder to Python's path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))

from config import GEMINI_API_KEY

api_key = (GEMINI_API_KEY or os.getenv("GEMINI_API_KEY", "")).strip()
print(f"API Key found: {api_key[:8]}... (Total length: {len(api_key)})")

if not api_key or api_key.startswith("your_"):
    print("[ERROR] No valid GEMINI_API_KEY found in backend/config.py!")
    sys.exit(1)

# Test 1: Try official google-genai
print("\n--- Testing Official SDK (google-genai) ---")
try:
    from google import genai
    client = genai.Client(api_key=api_key)
    res = client.models.generate_content(
        model="gemini-3.6-flash",
        contents="Say hello in one word."
    )
    print(f"Official SDK Result: {res.text.strip()}")
except Exception as e:
    print(f"Official SDK Error: {e}")

# Test 2: Try legacy google.generativeai
print("\n--- Testing Legacy SDK (google.generativeai) ---")
try:
    import google.generativeai as genai_leg
    genai_leg.configure(api_key=api_key)
    model = genai_leg.GenerativeModel("gemini-2.5-flash")
    res = model.generate_content("Say hello in one word.")
    print(f"Legacy SDK Result: {res.text.strip()}")
except Exception as e:
    print(f"Legacy SDK Error: {e}")