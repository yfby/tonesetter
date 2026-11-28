import sys

from unsaid.cli import main
from unsaid.config import ConfigError
from unsaid.models import Relationship, Tone


def test_one_shot_prints_only_the_message(monkeypatch, capsys) -> None:
    monkeypatch.setattr(
        "unsaid.cli.rewrite", lambda request, model=None: "Thanks, but no."
    )
    monkeypatch.setattr(
        sys,
        "argv",
        ["unsaid", "--draft", "No.", "--scenario", "decline"],
    )

    assert main() == 0
    assert capsys.readouterr().out == "Thanks, but no.\n"


def test_errors_go_to_stderr(monkeypatch, capsys) -> None:
    def fail(*args: object, **kwargs: object) -> None:
        raise ConfigError("No Gemini API key found.")

    monkeypatch.setattr("unsaid.cli.rewrite", fail)
    monkeypatch.setattr(sys, "argv", ["unsaid", "--intent", "decline"])

    assert main() == 1
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "No Gemini API key found." in captured.err


def test_interactive_mode_collects_context(monkeypatch, capsys) -> None:
    answers = iter(["", "colleague", "direct", "", "I need to decline"])
    monkeypatch.setattr("builtins.input", lambda: next(answers))
    seen: dict = {}

    def fake_rewrite(request, model=None):
        seen["request"] = request
        return "Okay."

    monkeypatch.setattr("unsaid.cli.rewrite", fake_rewrite)
    monkeypatch.setattr(sys, "argv", ["unsaid"])

    assert main() == 0
    request = seen["request"]
    assert request.relationship is Relationship.COLLEAGUE
    assert request.tone is Tone.DIRECT
    assert request.intent == "I need to decline"
    assert capsys.readouterr().out == "Okay.\n"


def test_empty_input_is_rejected(monkeypatch, capsys) -> None:
    monkeypatch.setattr(sys, "argv", ["unsaid", "--draft", "   "])

    assert main() == 1
    assert "Provide a draft, an intent, or both" in capsys.readouterr().err
