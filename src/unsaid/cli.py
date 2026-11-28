"""Command-line interface: interactive by default, flags for one-shot use."""

from __future__ import annotations

import argparse
import sys
from enum import Enum
from typing import TypeVar

from .config import DEFAULT_MODEL, ConfigError
from .models import Relationship, RewriteRequest, Scenario, Tone
from .service import ServiceError, rewrite

EnumT = TypeVar("EnumT", bound=Enum)


def _input(prompt: str) -> str:
    """Prompt on stderr so stdout stays reserved for the final message."""
    print(prompt, end="", file=sys.stderr, flush=True)
    return input()


def _select(label: str, enum_type: type[EnumT], default: EnumT) -> EnumT:
    options = ", ".join(member.value for member in enum_type)
    while True:
        answer = _input(f"{label} [{options}] ({default.value}): ").strip().lower()
        if not answer:
            return default
        try:
            return enum_type(answer)
        except ValueError:
            print(f"Please choose one of: {options}", file=sys.stderr)


def _read_draft() -> str:
    print(
        "Draft (paste it, then press Enter on an empty line; "
        "leave blank to write from scratch):",
        file=sys.stderr,
    )
    lines: list[str] = []
    while True:
        try:
            line = input()
        except EOFError:
            break
        if not line.strip():
            break
        lines.append(line)
    return "\n".join(lines).strip()


def _interactive_request(args: argparse.Namespace) -> RewriteRequest:
    print("Unsaid: describe what you want to say.\n", file=sys.stderr)
    scenario = _select("Scenario", Scenario, args.scenario or Scenario.OTHER)
    relationship = _select(
        "Relationship", Relationship, args.relationship or Relationship.FRIEND
    )
    tone = _select("Tone", Tone, args.tone or Tone.BALANCED)

    draft = _read_draft()
    if draft:
        intent = _input("Anything to add or change? (optional): ").strip()
    else:
        while True:
            intent = _input("What do you want to say? (situation and goal): ").strip()
            if intent:
                break
            print("Please describe what you want to say.", file=sys.stderr)

    return RewriteRequest(
        scenario=scenario,
        relationship=relationship,
        tone=tone,
        draft=draft,
        intent=intent,
    )


def _one_shot_request(args: argparse.Namespace) -> RewriteRequest:
    return RewriteRequest(
        scenario=args.scenario or Scenario.OTHER,
        relationship=args.relationship or Relationship.FRIEND,
        tone=args.tone or Tone.BALANCED,
        draft=args.draft or "",
        intent=args.intent or "",
    )


def _choices(enum_type: type[Enum]) -> list[str]:
    return [member.value for member in enum_type]


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="unsaid",
        description="Rewrite a delicate message so it lands the way you mean it.",
    )
    parser.add_argument("--draft", help="Message you want to polish (one-shot mode)")
    parser.add_argument(
        "--intent", help="What you actually want to say (one-shot mode)"
    )
    parser.add_argument(
        "--scenario",
        type=Scenario,
        choices=_choices(Scenario),
        help="boundary, decline, disappointment, or other",
    )
    parser.add_argument(
        "--relationship",
        type=Relationship,
        choices=_choices(Relationship),
        help="friend, colleague, family, acquaintance, or other",
    )
    parser.add_argument(
        "--tone",
        type=Tone,
        choices=_choices(Tone),
        help="gentle, balanced, or direct",
    )
    parser.add_argument(
        "--model",
        help=f"Gemini model to use (default: {DEFAULT_MODEL})",
    )
    return parser


def main() -> int:
    args = _parser().parse_args()
    try:
        request = (
            _one_shot_request(args)
            if args.draft is not None or args.intent is not None
            else _interactive_request(args)
        )
        message = rewrite(request, model=args.model)
    except (ConfigError, ServiceError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    except (KeyboardInterrupt, EOFError):
        print("\nCancelled.", file=sys.stderr)
        return 130

    print(message)
    return 0
