"""Tries each model once with the app's own settings. Run: python test_models.py"""
import time

from google import genai
from google.genai import errors, types

from backend.core.config import GEMINI_API_KEY
from backend.services import prompts

MODELS = [
    "gemini-2.5-flash",
    "gemini-2.5-flash-lite",
    "gemini-flash-latest",
    "gemini-flash-lite-latest",
    "gemini-3.1-flash-lite",
    "gemini-3.5-flash-lite",
    "gemini-3.5-flash",
]

client = genai.Client(api_key=GEMINI_API_KEY, http_options=types.HttpOptions(timeout=25000))

for model in MODELS:
    start = time.time()
    try:
        client.models.generate_content(
            model=model,
            contents="how to plan event",
            config=types.GenerateContentConfig(
                system_instruction=prompts.CHAT_SYSTEM, temperature=0.6
            ),
        )
        print(f"{model}: OK in {time.time() - start:.1f}s")
    except errors.APIError as error:
        print(f"{model}: API error {error.code} {error.status} after {time.time() - start:.1f}s")
    except Exception as error:
        print(f"{model}: {type(error).__name__} after {time.time() - start:.1f}s")
    time.sleep(1)