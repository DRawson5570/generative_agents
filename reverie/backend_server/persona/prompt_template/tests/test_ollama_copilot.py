import os
import requests

# flake8: noqa: E402
import pytest

# Ensure reverie path for tests
import sys
import pathlib
ROOT = str(pathlib.Path(__file__).resolve().parents[3])
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import persona.prompt_template.gpt_structure as gs


class DummyResp:
    def __init__(self, status=200, json_body=None, text=""):
        self._status = status
        self._json = json_body
        self.text = text

    def raise_for_status(self):
        if self._status >= 400:
            raise requests.HTTPError("status")

    def json(self):
        if self._json is None:
            raise ValueError("no json")
        return self._json


def test_ollama_request_retries_then_success(monkeypatch):
    calls = {"n": 0}

    def fake_post(url, json, timeout):
        calls["n"] += 1
        if calls["n"] < 2:
            raise requests.ConnectionError("connect")
        return DummyResp(json_body={"results": [{"content": "ollama-output"}]})

    monkeypatch.setattr(requests, "post", fake_post)
    out = gs.Ollama_request("hello", model="foo", timeout=0.1, repeat=3)
    assert out == "ollama-output"
    assert calls["n"] == 2


def test_ollama_request_parsing_variants(monkeypatch):
    def fake_post_a(url, json, timeout):
        return DummyResp(json_body={"output": "outA"})

    def fake_post_b(url, json, timeout):
        return DummyResp(json_body={"text": "outB"})

    monkeypatch.setattr(requests, "post", fake_post_a)
    assert gs.Ollama_request("p1") == "outA"

    monkeypatch.setattr(requests, "post", fake_post_b)
    assert gs.Ollama_request("p2") == "outB"


def test_copilot_request_requires_url(monkeypatch):
    # ensure env is unset
    monkeypatch.delenv("COPILOT_API_URL", raising=False)
    with pytest.raises(RuntimeError):
        gs.Copilot_request("p")


def test_copilot_request_with_url(monkeypatch):
    monkeypatch.setenv("COPILOT_API_URL", "http://example/api")

    def fake_post(url, json, headers, timeout):
        return DummyResp(json_body={"result": "copilot-out"})

    monkeypatch.setattr(requests, "post", fake_post)
    out = gs.Copilot_request("p")
    assert out == "copilot-out"
