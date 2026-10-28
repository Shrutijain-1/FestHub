"""The ONLY file that talks to Gemini. Everything else calls these functions."""
import logging
import time

from google import genai
from google.genai import errors, types

from backend.core.config import GEMINI_API_KEY, GEMINI_FALLBACK_MODEL, GEMINI_MODEL
from backend.schemas.ai import (
    ChatRequest, ChecklistRequest, EventBrief, IdeasRequest, InvitationRequest,
)
from backend.services import prompts

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("eventflow.ai")

REQUEST_TIMEOUT_MS = 25000     # each Gemini call may take up to 25 seconds
RETRY_CODES = {500, 502, 503, 504}  # temporary Google-side problems


class AIServiceError(Exception):
    """Carries a friendly message and the HTTP status to return."""

    def __init__(self, message: str, status_code: int = 503):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


_client: genai.Client | None = None


def _get_client() -> genai.Client:
    global _client
    if not GEMINI_API_KEY:
        raise AIServiceError(
            "AI is not set up yet. Add GEMINI_API_KEY to the .env file and restart the backend."
        )
    if _client is None:
        _client = genai.Client(
            api_key=GEMINI_API_KEY,
            http_options=types.HttpOptions(timeout=REQUEST_TIMEOUT_MS),
        )
    return _client


def _friendly(error: errors.APIError) -> AIServiceError:
    code = getattr(error, "code", None)
    if code == 429:
        return AIServiceError("The AI usage limit was reached. Please wait a minute and try again.", 429)
    if code in (400, 401, 403):
        return AIServiceError("The AI key is invalid or not allowed. Check GEMINI_API_KEY in .env.")
    if code == 404:
        return AIServiceError("The AI model was not found. Check GEMINI_MODEL in .env.")
    if code == 504:
        return AIServiceError("The AI took too long to answer. Please try again.", 504)
    return AIServiceError("The AI service is busy right now. Please try again shortly.")


def _network_error(error: Exception) -> AIServiceError:
    """For failures that are not Gemini API errors, such as timeouts and dropped connections."""
    if "timeout" in type(error).__name__.lower():
        return AIServiceError("The AI took too long to answer. Please try again.", 504)
    return AIServiceError("The AI service could not be reached. Please try again.")


def _generate(contents, system: str, temperature: float = 0.7) -> str:
    """Try the main model, then the backup model. Log every outcome."""
    client = _get_client()
    models_to_try = [GEMINI_MODEL, GEMINI_FALLBACK_MODEL]
    response = None
    last_error: AIServiceError | None = None

    for attempt, model in enumerate(models_to_try, start=1):
        try:
            response = client.models.generate_content(
                model=model,
                contents=contents,
                config=types.GenerateContentConfig(
                    system_instruction=system, temperature=temperature,
                ),
            )
            logger.info("Gemini OK: attempt=%s model=%s", attempt, model)
            break
        except errors.APIError as error:
            code = getattr(error, "code", None)
            logger.warning(
                "Gemini API error: attempt=%s model=%s code=%s message=%s",
                attempt, model, code, getattr(error, "message", ""),
            )
            last_error = _friendly(error)
            # A bad key can't be fixed by another model, so stop. Server errors,
            # a wrong model name (404) and a model's own quota (429) move on to the backup.
            if code not in RETRY_CODES and code not in (404, 429):
                raise last_error
        except Exception as error:
            logger.exception(
                "Gemini call failed (not an API error): attempt=%s model=%s", attempt, model
            )
            last_error = _network_error(error)

        if attempt < len(models_to_try):
            time.sleep(1)

    if response is None:
        raise last_error or AIServiceError("The AI service is busy right now. Please try again shortly.")

    text = (response.text or "").strip()
    if not text:
        raise AIServiceError(
            "The AI did not return an answer. The request may have been blocked, so try rewording it.", 422
        )
    return text


# ---------- One function per feature ----------

def generate_description(brief: EventBrief) -> str:
    return _generate(prompts.description(brief), prompts.GENERATION_SYSTEM)


def generate_highlights(brief: EventBrief) -> str:
    return _generate(prompts.highlights(brief), prompts.GENERATION_SYSTEM)


def generate_schedule(brief: EventBrief) -> str:
    return _generate(prompts.schedule(brief), prompts.GENERATION_SYSTEM, temperature=0.4)


def generate_invitation(request: InvitationRequest) -> str:
    return _generate(prompts.invitation(request), prompts.GENERATION_SYSTEM)


def generate_checklist(request: ChecklistRequest) -> str:
    return _generate(prompts.checklist(request), prompts.GENERATION_SYSTEM, temperature=0.4)


def event_ideas(request: IdeasRequest) -> str:
    return _generate(prompts.ideas(request.prompt), prompts.GENERATION_SYSTEM)


def chat(request: ChatRequest) -> str:
    """Stateless: the frontend sends the recent messages each time."""
    contents = [
        types.Content(
            role="model" if m.role == "assistant" else "user",
            parts=[types.Part(text=m.content)],
        )
        for m in request.history[-10:]
    ]
    while contents and contents[0].role == "model":
        contents.pop(0)  # a conversation must start with the user
    contents.append(types.Content(role="user", parts=[types.Part(text=request.message)]))
    return _generate(contents, prompts.CHAT_SYSTEM, temperature=0.6)