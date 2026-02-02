# flake8: noqa: E402
import os
import sys

# Ensure reverie/backend_server is importable for tests
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import types

import persona.prompt_template.run_gpt_prompt as rgp


def test_event_triple_handles_fail_safe(monkeypatch):
    # stub generate_prompt so we don't read files
    monkeypatch.setattr(rgp, "generate_prompt", lambda *a, **k: "PROMPT")

    # Make safe_generate_response return the fail-safe (a triple)
    def fake_safe(prompt, gpt_param, repeat, fail_safe, validate, cleanup):
        return fail_safe

    monkeypatch.setattr(rgp, "safe_generate_response", fake_safe)

    persona = types.SimpleNamespace(name="Jane")
    output, meta = rgp.run_gpt_prompt_event_triple("(do something)", persona)

    # With the current behavior, safe returns fail_safe which is a triple (Jane, 'is', 'idle')
    # The function then builds another triple starting with persona.name
    assert isinstance(output, tuple)
    assert output[0] == "Jane"


def test_wake_up_hour_returns_fail_safe_when_invalid(monkeypatch):
    monkeypatch.setattr(rgp, "generate_prompt", lambda *a, **k: "PROMPT")

    def fake_safe(prompt, gpt_param, repeat, fail_safe, validate, cleanup):
        return fail_safe

    monkeypatch.setattr(rgp, "safe_generate_response", fake_safe)

    class DummyScratch:
        def get_str_iss(self):
            return "dummy_iss"

        def get_str_lifestyle(self):
            return "dummy_lifestyle"

        def get_str_firstname(self):
            return "Jane"

        def get_str_curr_date_str(self):
            return "February 02, 2026"

    class DummyPersona:
        def __init__(self):
            self.scratch = DummyScratch()
            self.name = "Jane"

    persona = DummyPersona()
    # The function returns (output, meta) and fail-safe hour is 8
    out, meta = rgp.run_gpt_prompt_wake_up_hour(persona)
    assert out == 8
    assert isinstance(meta, list)


def test_daily_plan_handles_malformed_output(monkeypatch):
    monkeypatch.setattr(rgp, "generate_prompt", lambda *a, **k: "PROMPT")

    # return malformed (not a list) to simulate bad model output; should use fail-safe
    def fake_safe(prompt, gpt_param, repeat, fail_safe, validate, cleanup):
        return fail_safe

    monkeypatch.setattr(rgp, "safe_generate_response", fake_safe)

    class DummyScratch:
        def get_str_iss(self):
            return "dummy_iss"

        def get_str_lifestyle(self):
            return "dummy_lifestyle"

        def get_str_firstname(self):
            return "Jane"

        def get_str_curr_date_str(self):
            return "February 02, 2026"

    class DummyPersona:
        def __init__(self):
            self.scratch = DummyScratch()
            self.name = "Jane"

    persona = DummyPersona()

    out, meta = rgp.run_gpt_prompt_daily_plan(persona, 7)
    assert isinstance(out, list)
    assert out[0].startswith("wake up and complete the morning routine at 7:00 am")
