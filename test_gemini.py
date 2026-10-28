"""Quick Gemini check. Run: python test_gemini.py"""
from google import genai
from google.genai import errors

from backend.core.config import GEMINI_API_KEY, GEMINI_MODEL

client = genai.Client(api_key=GEMINI_API_KEY)
print("Model:", GEMINI_MODEL)

try:
    reply = client.models.generate_content(
        model=GEMINI_MODEL, contents="Say hello in five words."
    )
    print("OK:", reply.text)
except errors.APIError as error:
    print("API error code:", error.code)
    print("Status:", error.status)
    print("Message:", error.message)
except Exception as error:
    print(type(error).__name__, error)

print("\nModels available to your key:")
try:
    for model in client.models.list():
        print(" ", model.name)
except Exception as error:
    print("Could not list models:", type(error).__name__)