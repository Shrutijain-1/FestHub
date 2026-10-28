"""AI endpoints. They check who is asking, then hand over to gemini_service."""
from fastapi import APIRouter, Depends, HTTPException

from backend.auth.dependencies import get_current_user, require_organizer
from backend.models import User
from backend.schemas.ai import (
    AIResponse, ChatRequest, ChecklistRequest, EventBrief, IdeasRequest, InvitationRequest,
)
from backend.services import gemini_service
from backend.services.gemini_service import AIServiceError

router = APIRouter(prefix="/api/ai", tags=["AI"])


def _respond(function, *args) -> AIResponse:
    try:
        return AIResponse(text=function(*args))
    except AIServiceError as error:
        raise HTTPException(status_code=error.status_code, detail=error.message)


# Organizer-only tools
@router.post("/generate-description", response_model=AIResponse)
def generate_description(payload: EventBrief, user: User = Depends(require_organizer)):
    return _respond(gemini_service.generate_description, payload)


@router.post("/generate-highlights", response_model=AIResponse)
def generate_highlights(payload: EventBrief, user: User = Depends(require_organizer)):
    return _respond(gemini_service.generate_highlights, payload)


@router.post("/generate-schedule", response_model=AIResponse)
def generate_schedule(payload: EventBrief, user: User = Depends(require_organizer)):
    return _respond(gemini_service.generate_schedule, payload)


@router.post("/generate-invitation", response_model=AIResponse)
def generate_invitation(payload: InvitationRequest, user: User = Depends(require_organizer)):
    return _respond(gemini_service.generate_invitation, payload)


@router.post("/generate-checklist", response_model=AIResponse)
def generate_checklist(payload: ChecklistRequest, user: User = Depends(require_organizer)):
    return _respond(gemini_service.generate_checklist, payload)


# Any logged-in user
@router.post("/event-ideas", response_model=AIResponse)
def event_ideas(payload: IdeasRequest, user: User = Depends(get_current_user)):
    return _respond(gemini_service.event_ideas, payload)


@router.post("/chat", response_model=AIResponse)
def chat(payload: ChatRequest, user: User = Depends(get_current_user)):
    return _respond(gemini_service.chat, payload)