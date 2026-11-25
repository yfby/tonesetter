"""Data shapes for a Tonesetter rewrite request and result."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field, model_validator


class Scenario(str, Enum):
    BOUNDARY = "boundary"
    DECLINE = "decline"
    DISAPPOINTMENT = "disappointment"
    OTHER = "other"


class Relationship(str, Enum):
    FRIEND = "friend"
    COLLEAGUE = "colleague"
    FAMILY = "family"
    ACQUAINTANCE = "acquaintance"
    OTHER = "other"


class Tone(str, Enum):
    GENTLE = "gentle"
    BALANCED = "balanced"
    DIRECT = "direct"


class RewriteRequest(BaseModel):
    """Everything the model needs to write one message."""

    scenario: Scenario = Scenario.OTHER
    relationship: Relationship = Relationship.FRIEND
    tone: Tone = Tone.BALANCED
    draft: str = ""
    intent: str = ""

    @model_validator(mode="after")
    def has_something_to_say(self) -> RewriteRequest:
        if not self.draft.strip() and not self.intent.strip():
            raise ValueError("Provide a draft, an intent, or both.")
        return self


class RewriteResult(BaseModel):
    """Only the message is returned; no commentary leaks into the output."""

    rewritten_message: str = Field(
        description="The final message, ready to copy and send."
    )
