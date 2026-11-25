import pytest
from pydantic import ValidationError

from tonesetter.models import RewriteRequest


def test_requires_a_draft_or_an_intent() -> None:
    with pytest.raises(ValidationError):
        RewriteRequest()


def test_accepts_a_draft_only() -> None:
    request = RewriteRequest(draft="No thanks.")
    assert request.draft == "No thanks."
    assert request.intent == ""


def test_accepts_an_intent_only() -> None:
    request = RewriteRequest(intent="decline the invitation")
    assert request.intent == "decline the invitation"


def test_whitespace_does_not_count_as_content() -> None:
    with pytest.raises(ValidationError):
        RewriteRequest(draft="   \n", intent="  ")
