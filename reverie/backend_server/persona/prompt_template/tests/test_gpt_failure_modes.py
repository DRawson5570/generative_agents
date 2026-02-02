# flake8: noqa: E402
import os
import sys

# Ensure reverie/backend_server is importable for tests
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import types
import json
import openai

import persona.prompt_template.gpt_structure as gs


def test_chatgpt_request_retries_then_success(monkeypatch):
    calls = {"n": 0}

    def fake_create(**kw):
        calls["n"] += 1
        if calls["n"] < 3:
            raise Exception("rate limit")
        return {"choices": [{"message": {"content": "ok-response"}}]}

    monkeypatch.setattr(openai.ChatCompletion, "create", fake_create)

    # Should retry and eventually succeed
    out = gs.ChatGPT_request("hello", timeout=1, repeat=3)
    assert out == "ok-response"
    assert calls["n"] == 3


def test_chatgpt_request_all_fail_returns_error(monkeypatch):
    def fake_create(**kw):
        raise Exception("server down")

    monkeypatch.setattr(openai.ChatCompletion, "create", fake_create)

    out = gs.ChatGPT_request("hello", timeout=0.1, repeat=2)
    assert out == "ChatGPT ERROR"


def test_chatgpt_safe_generate_response_parsing_failure(monkeypatch):
    # ChatGPT_request returns malformed JSON repeatedly
    responses = ["not a json", "still not json"]

    def fake_chat_request(prompt):
        return responses.pop(0) if responses else ""

    monkeypatch.setattr(gs, "ChatGPT_request", fake_chat_request)

    def validate(x, prompt=""):
        return True

    def cleanup(x, prompt=""):
        return x

    out = gs.ChatGPT_safe_generate_response("p", "ex", "ins", repeat=2, func_validate=validate, func_clean_up=cleanup)
    assert out is False


def test_chatgpt_safe_generate_response_success_after_retry(monkeypatch):
    # First response malformed, second valid JSON
    responses = ["garbage", json.dumps({"output": "GOOD"})]

    def fake_chat_request(prompt):
        return responses.pop(0)

    monkeypatch.setattr(gs, "ChatGPT_request", fake_chat_request)

    def validate(x, prompt=""):
        return True

    def cleanup(x, prompt=""):
        return x

    out = gs.ChatGPT_safe_generate_response("p", "ex", "ins", repeat=3, func_validate=validate, func_clean_up=cleanup)
    assert out == "GOOD"
