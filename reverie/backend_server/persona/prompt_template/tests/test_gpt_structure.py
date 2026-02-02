# flake8: noqa: E402,F401
import os
import sys

# Make sure reverie/backend_server is importable for tests
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import json

from persona.prompt_template import gpt_structure as gs


def test_generate_prompt(tmp_path):
    # create a tiny prompt file
    p = tmp_path / "prompt_lib.txt"
    p.write_text("Header\n!<INPUT 0>!\nFooter")
    prompt = gs.generate_prompt(["hello world"], str(p))
    assert "hello world" in prompt


def test_chatgpt_request_success(monkeypatch):
    def fake_create(**kwargs):
        # mirror the OpenAI response shape as a plain dict
        return {"choices": [{"message": {"content": "fake response"}}]}

    monkeypatch.setattr(gs.openai.ChatCompletion, "create", fake_create)
    out = gs.ChatGPT_request("hi", timeout=1, repeat=1)
    assert out == "fake response"


def test_gpt4_request_failure(monkeypatch):
    def failing_create(**kwargs):
        raise RuntimeError("down")

    monkeypatch.setattr(gs.openai.ChatCompletion, "create", failing_create)
    out = gs.GPT4_request("hi", timeout=1, repeat=1)
    assert out == "ChatGPT ERROR"
