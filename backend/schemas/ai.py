"""Request and response shapes for the AI endpoints."""
from typing import Literal

from pydantic import BaseModel, Field


class EventBrief(BaseModel):
    """The basic facts about an event, shared by most AI tools."""
    title: str = Field(min_length=3, max_length=200)
    event_type: str = Field(default="Other", max_length=50)
    audience: str = Field(min_length=2, max_length=150)
    duration: str | None = Field(default=None, max_length=100)
    college: str | None = Field(default=None, max_length=150)
    notes: str | None = Field(default=None, max_length=500)


class InvitationRequest(EventBrief):
    channel: Literal["whatsapp", "email", "social"]
    date_text: str | None = Field(default=None, max_length=100)
    venue: str | None = Field(default=None, max_length=200)


class ChecklistRequest(EventBrief):
    attendees: int = Field(default=100, ge=1, le=100000)


class IdeasRequest(BaseModel):
    prompt: str = Field(min_length=5, max_length=500)


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=4000)


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=1000)
    history: list[ChatMessage] = Field(default_factory=list, max_length=20)


class AIResponse(BaseModel):
    text: str