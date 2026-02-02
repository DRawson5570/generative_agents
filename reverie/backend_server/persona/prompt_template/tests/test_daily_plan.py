# flake8: noqa: E402
import os
import sys

# Make sure reverie/backend_server is importable for tests
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from persona.prompt_template import run_gpt_prompt as rgp


class DummyScratch:
    def __init__(self):
        pass

    def get_str_iss(self):
        return "dummy_iss"

    def get_str_lifestyle(self):
        return "dummy_lifestyle"

    def get_str_curr_date_str(self):
        return "Monday January 1"

    def get_str_firstname(self):
        return "Jane"


class DummyPersona:
    def __init__(self):
        self.scratch = DummyScratch()
        self.name = "Jane Doe"


def test_daily_plan_default(monkeypatch):
    persona = DummyPersona()

    def fake_generate_prompt(prompt_input, template):
        assert isinstance(prompt_input, list)
        return "PROMPT_DAILY"

    monkeypatch.setattr(rgp, "generate_prompt", fake_generate_prompt)

    # fake safe_generate_response to return list of actions (without wake up)
    def fake_safe_generate_response(prompt, gpt_param, repeat, fail_safe, func_validate, func_clean_up):
        # simulate GPT returning two actions formatted as the cleanup expects
        return ["eat breakfast at 7:00 am", "do exercise at 8:00 am"]

    monkeypatch.setattr(rgp, "safe_generate_response", fake_safe_generate_response)

    out, meta = rgp.run_gpt_prompt_daily_plan(persona, 6)
    assert out[0].startswith("wake up and complete the morning routine at 6:00 am")
    assert "eat breakfast" in out[1]
    assert meta[1] == "PROMPT_DAILY"


def test_daily_plan_with_test_input(monkeypatch):
    persona = DummyPersona()

    def fake_generate_prompt(prompt_input, template):
        # when test_input is provided, create_prompt_input returns test_input directly
        assert prompt_input == "TEST_INPUT"
        return "PROMPT_DAILY_TEST"

    monkeypatch.setattr(rgp, "generate_prompt", fake_generate_prompt)

    def fake_safe_generate_response(prompt, gpt_param, repeat, fail_safe, func_validate, func_clean_up):
        return ["custom action at 9:00 am"]

    monkeypatch.setattr(rgp, "safe_generate_response", fake_safe_generate_response)

    out, meta = rgp.run_gpt_prompt_daily_plan(persona, 7, test_input="TEST_INPUT")
    assert out[0].startswith("wake up and complete the morning routine at 7:00 am")
    assert "custom action" in out[1]
    assert meta[1] == "PROMPT_DAILY_TEST"
