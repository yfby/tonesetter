from types import SimpleNamespace

import pytest
from google.genai import errors

from unsaid import service
from unsaid.models import RewriteRequest, RewriteResult
from unsaid.service import ServiceError, rewrite


class _Models:
    def __init__(self, response: object) -> None:
        self.response = response
        self.calls: list[dict] = []

    def generate_content(self, **kwargs: object) -> object:
        self.calls.append(kwargs)
        return self.response


class _Client:
    def __init__(self, response: object) -> None:
        self.models = _Models(response)


def test_rewrite_returns_only_the_message() -> None:
    client = _Client(
        SimpleNamespace(parsed=RewriteResult(rewritten_message="  No thanks!  "))
    )

    message = rewrite(
        RewriteRequest(intent="decline"),
        client=client,
        model="test-model",
    )

    assert message == "No thanks!"
    call = client.models.calls[0]
    assert call["model"] == "test-model"
    assert call["config"].response_schema is RewriteResult
    assert call["config"].response_mime_type == "application/json"
    assert "Scenario: other" in call["contents"]


def test_rewrite_accepts_a_parsed_dict() -> None:
    client = _Client(SimpleNamespace(parsed={"rewritten_message": "I can't."}))
    assert rewrite(RewriteRequest(draft="I can't."), client=client, model="m") == "I can't."


@pytest.mark.parametrize("parsed", [None, {"rewritten_message": "   "}])
def test_rewrite_rejects_unusable_responses(parsed: object) -> None:
    client = _Client(SimpleNamespace(parsed=parsed))
    with pytest.raises(ServiceError):
        rewrite(RewriteRequest(intent="decline"), client=client, model="m")


def test_rewrite_wraps_api_errors() -> None:
    class BrokenModels:
        def generate_content(self, **kwargs: object) -> object:
            raise RuntimeError("quota exceeded")

    client = SimpleNamespace(models=BrokenModels())
    with pytest.raises(ServiceError, match="quota exceeded"):
        rewrite(RewriteRequest(intent="decline"), client=client, model="m")


class _FlakyModels:
    def __init__(self, outcomes: list[object]) -> None:
        self.outcomes = outcomes
        self.calls: list[str] = []

    def generate_content(self, **kwargs: object) -> object:
        self.calls.append(str(kwargs["model"]))
        outcome = self.outcomes.pop(0)
        if isinstance(outcome, Exception):
            raise outcome
        return SimpleNamespace(parsed=RewriteResult(rewritten_message=outcome))


def _overloaded() -> errors.APIError:
    return errors.APIError(
        503, {"error": {"status": "UNAVAILABLE", "message": "high demand"}}
    )


def test_falls_back_on_503(monkeypatch) -> None:
    monkeypatch.setattr(service, "fallback_models", lambda: ["fallback-model"])
    models = _FlakyModels([_overloaded(), "Fallback message."])
    client = SimpleNamespace(models=models)

    message = rewrite(
        RewriteRequest(intent="decline"), client=client, model="primary"
    )

    assert message == "Fallback message."
    assert models.calls == ["primary", "fallback-model"]


def test_other_api_errors_do_not_fall_back(monkeypatch) -> None:
    monkeypatch.setattr(service, "fallback_models", lambda: ["fallback-model"])
    quota_error = errors.APIError(
        429, {"error": {"status": "RESOURCE_EXHAUSTED", "message": "quota"}}
    )
    models = _FlakyModels([quota_error, "should not be used"])
    client = SimpleNamespace(models=models)

    with pytest.raises(ServiceError, match="quota"):
        rewrite(RewriteRequest(intent="decline"), client=client, model="primary")

    assert models.calls == ["primary"]


def test_reports_when_every_model_is_overloaded(monkeypatch) -> None:
    monkeypatch.setattr(
        service, "fallback_models", lambda: ["fallback-a", "fallback-b"]
    )
    models = _FlakyModels([_overloaded(), _overloaded(), _overloaded()])
    client = SimpleNamespace(models=models)

    with pytest.raises(ServiceError, match="all attempted models"):
        rewrite(RewriteRequest(intent="decline"), client=client, model="primary")

    assert models.calls == ["primary", "fallback-a", "fallback-b"]


def test_duplicate_fallback_is_skipped(monkeypatch) -> None:
    monkeypatch.setattr(service, "fallback_models", lambda: ["primary", "fallback"])
    models = _FlakyModels([_overloaded(), "Done."])
    client = SimpleNamespace(models=models)

    rewrite(RewriteRequest(intent="decline"), client=client, model="primary")

    assert models.calls == ["primary", "fallback"]
