import types

from persona.prompt_template.run_gpt_prompt import (
    run_gpt_prompt_pronunciatio,
    run_gpt_prompt_event_triple,
)


def test_pronunciatio_returns_emoji(monkeypatch):
    """ChatGPT plugin path should return an emoji string via ChatGPT_safe_generate_response"""

    def fake_chatgpt(prompt, example_output, special_instruction, attempts, fail_safe, validate, cleanup, flag):
        return "🙂"

    monkeypatch.setattr(
        "persona.prompt_template.run_gpt_prompt.ChatGPT_safe_generate_response",
        fake_chatgpt,
    )

    persona = types.SimpleNamespace(name="Jane")

    # Avoid opening prompt template files during tests
    monkeypatch.setattr(
        "persona.prompt_template.run_gpt_prompt.generate_prompt",
        lambda *a, **k: "PROMPT",
    )

    output, meta = run_gpt_prompt_pronunciatio("make breakfast", persona)

    assert output == "🙂"
    assert isinstance(meta, list)


def test_event_triple_returns_triple(monkeypatch):
    """safe_generate_response should return a two-element list that becomes a triple"""

    def fake_safe_generate(prompt, gpt_param, attempts, fail_safe, validate, cleanup):
        return ["cooking", "breakfast"]

    monkeypatch.setattr(
        "persona.prompt_template.run_gpt_prompt.safe_generate_response",
        fake_safe_generate,
    )

    persona = types.SimpleNamespace(name="Jane")

    # Avoid opening prompt template files during tests
    monkeypatch.setattr(
        "persona.prompt_template.run_gpt_prompt.generate_prompt",
        lambda *a, **k: "PROMPT",
    )

    output, meta = run_gpt_prompt_event_triple("(do something)", persona)

    assert output == ("Jane", "cooking", "breakfast")
    assert isinstance(meta, list)
