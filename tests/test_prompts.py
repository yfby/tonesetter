from unsaid.models import Relationship, RewriteRequest, Scenario, Tone
from unsaid.prompts import SYSTEM_INSTRUCTION, build_prompt


def test_prompt_includes_context_and_content() -> None:
    request = RewriteRequest(
        scenario=Scenario.DECLINE,
        relationship=Relationship.COLLEAGUE,
        tone=Tone.GENTLE,
        draft="Can't make it.",
        intent="Need to leave on time.",
    )
    prompt = build_prompt(request)

    assert "Scenario: decline" in prompt
    assert "Relationship: colleague" in prompt
    assert "Desired tone: gentle" in prompt
    assert "Channel:" not in prompt
    assert "Can't make it." in prompt
    assert "Need to leave on time." in prompt


def test_prompt_handles_missing_parts() -> None:
    prompt = build_prompt(RewriteRequest(intent="set a boundary"))
    assert "Draft from user:\n(none)" in prompt
    assert "What the user wants to say:\nset a boundary" in prompt


def test_system_instruction_covers_all_three_scenarios() -> None:
    for scenario in ("boundary", "decline", "disappointment"):
        assert scenario in SYSTEM_INSTRUCTION
