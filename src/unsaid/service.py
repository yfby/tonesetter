"""Gemini calls with fallback to other models when one is overloaded."""

from __future__ import annotations

from google.genai import errors, types

from .config import fallback_models, make_client, model_name
from .models import RewriteRequest, RewriteResult
from .prompts import SYSTEM_INSTRUCTION, build_prompt


class ServiceError(RuntimeError):
    """Raised when Gemini returns nothing usable or every model fails."""


def _is_overloaded(exc: errors.APIError) -> bool:
    return exc.code == 503 or exc.status == "UNAVAILABLE"


def _candidate_models(primary: str) -> list[str]:
    models = [primary]
    for candidate in fallback_models():
        if candidate not in models:
            models.append(candidate)
    return models


def _generate(client: object, model: str, request: RewriteRequest) -> str:
    try:
        response = client.models.generate_content(  # type: ignore[attr-defined]
            model=model,
            contents=build_prompt(request),
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_INSTRUCTION,
                response_mime_type="application/json",
                response_schema=RewriteResult,
                temperature=0.7,
            ),
        )
    except errors.APIError:
        raise
    except Exception as exc:
        raise ServiceError(f"Gemini request failed: {exc}") from exc

    parsed = response.parsed
    if parsed is None:
        raise ServiceError("Gemini returned no message. Try again.")

    result = (
        parsed
        if isinstance(parsed, RewriteResult)
        else RewriteResult.model_validate(parsed)
    )
    message = result.rewritten_message.strip()
    if not message:
        raise ServiceError("Gemini returned an empty message. Try again.")
    return message


def rewrite(
    request: RewriteRequest,
    *,
    client: object | None = None,
    model: str | None = None,
) -> str:
    """Return the rewritten message, trying fallbacks on HTTP 503."""
    caller_client = client if client is not None else make_client()
    candidates = _candidate_models(model or model_name())
    last_overload: errors.APIError | None = None

    for candidate in candidates:
        try:
            return _generate(caller_client, candidate, request)
        except errors.APIError as exc:
            if not _is_overloaded(exc):
                raise ServiceError(f"Gemini request failed: {exc}") from exc
            last_overload = exc

    details = f": {last_overload}" if last_overload else ""
    raise ServiceError(
        f"Gemini is unavailable on all attempted models "
        f"({', '.join(candidates)}){details}"
    )
