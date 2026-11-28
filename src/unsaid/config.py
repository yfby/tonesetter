"""Environment configuration and Gemini client construction."""

from __future__ import annotations

import os

from dotenv import find_dotenv, load_dotenv
from google import genai

DEFAULT_MODEL = "gemini-4-hydrogen"
DEFAULT_FALLBACK_MODELS = ("gemini-3.5-flash-lite",)


class ConfigError(RuntimeError):
    """Raised when the tool is not configured to call Gemini."""


def _load_env() -> None:
    """Load .env without overriding variables already set in the shell."""
    load_dotenv(override=False)
    cwd_dotenv = find_dotenv(usecwd=True)
    if cwd_dotenv:
        load_dotenv(cwd_dotenv, override=False)


def api_key() -> str:
    _load_env()
    key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not key:
        raise ConfigError(
            "No Gemini API key found. Add GEMINI_API_KEY to .env "
            "(see .env.example), or export it in your shell."
        )
    return key


def model_name() -> str:
    _load_env()
    return os.environ.get("UNSAID_MODEL", DEFAULT_MODEL)


def fallback_models() -> list[str]:
    """Models to try when the primary model returns HTTP 503."""
    _load_env()
    raw = os.environ.get("UNSAID_FALLBACK_MODELS")
    if raw is None:
        return list(DEFAULT_FALLBACK_MODELS)
    return [name.strip() for name in raw.split(",") if name.strip()]


def make_client() -> genai.Client:
    return genai.Client(api_key=api_key())
