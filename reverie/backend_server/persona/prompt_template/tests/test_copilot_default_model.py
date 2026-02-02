# flake8: noqa: E402
import os
import types

# Ensure repo path for tests
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
            raise Exception("status")

    def json(self):
        return self._json


def test_copilot_uses_default_model_when_explicit_url(monkeypatch):
    captured = {}

    def fake_post(url, json, headers, timeout):
        captured['payload'] = json
        return DummyResp(json_body={"result": "ok"})

    monkeypatch.setenv("COPILOT_API_URL", "http://example/api")
    monkeypatch.setenv("COPILOT_DEFAULT_MODEL", "grok-code-fast-1")
    monkeypatch.setattr(gs.requests, "post", fake_post)

    out = gs.Copilot_request("hello")
    assert captured['payload']['model'] == "grok-code-fast-1"


def test_copilot_uses_default_model_when_token_exchange(monkeypatch):
    captured = {}

    # fake resolve_copilot_api_token to return baseUrl and token
    def fake_resolve(*a, **k):
        return {"token": "t", "baseUrl": "http://api.test"}

    def fake_post(url, json, headers, timeout):
        captured['url'] = url
        captured['payload'] = json
        captured['headers'] = headers
        return DummyResp(json_body={"result": "ok"})

    monkeypatch.delenv("COPILOT_API_URL", raising=False)
    monkeypatch.setenv("COPILOT_DEFAULT_MODEL", "grok-code-fast-1")
    monkeypatch.setattr(gs, "resolve_copilot_api_token", fake_resolve)
    monkeypatch.setattr(gs.requests, "post", fake_post)

    out = gs.Copilot_request("hello")
    assert captured['payload']['model'] == "grok-code-fast-1"
    assert 'Authorization' in captured['headers']
