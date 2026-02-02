# flake8: noqa: E402
import os
import sys

# Make sure reverie/backend_server is importable for tests
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import types

from persona.prompt_template import run_gpt_prompt as rgp


class DummyScratch:
    def __init__(self):
        pass

    def get_str_iss(self):
        return "dummy_iss"

    def get_str_lifestyle(self):
        return "dummy_lifestyle"

    def get_str_firstname(self):
        return "Jane"


class DummyPersona:
    def __init__(self):
        self.scratch = DummyScratch()
        self.name = "Jane Doe"


def test_wake_up_hour_default(monkeypatch):
    persona = DummyPersona()

    # fake generate_prompt to return a known prompt string
    def fake_generate_prompt(prompt_input, template):
        assert isinstance(prompt_input, list)
        return "PROMPT_DEFAULT"

    monkeypatch.setattr(rgp, "generate_prompt", fake_generate_prompt)

    # fake safe_generate_response to return an integer hour
    def fake_safe_generate_response(prompt, gpt_param, repeat, fail_safe, func_validate, func_clean_up):
        # Should call validate and cleanup internally; return cleaned value
        return func_clean_up("8am")

    monkeypatch.setattr(rgp, "safe_generate_response", fake_safe_generate_response)

    out, meta = rgp.run_gpt_prompt_wake_up_hour(persona)
    assert out == 8
    assert isinstance(meta, list)
    assert meta[1] == "PROMPT_DEFAULT"


def test_wake_up_hour_with_test_input(monkeypatch):
    persona = DummyPersona()

    def fake_generate_prompt(prompt_input, template):
        # When test_input is provided, run_gpt function passes it through
        assert prompt_input == "9am"
        return "PROMPT_TEST_INPUT"

    monkeypatch.setattr(rgp, "generate_prompt", fake_generate_prompt)

    def fake_safe_generate_response(prompt, gpt_param, repeat, fail_safe, func_validate, func_clean_up):
        return func_clean_up("9am")

    monkeypatch.setattr(rgp, "safe_generate_response", fake_safe_generate_response)

    out, meta = rgp.run_gpt_prompt_wake_up_hour(persona, test_input="9am")
    assert out == 9
    assert meta[1] == "PROMPT_TEST_INPUT"
