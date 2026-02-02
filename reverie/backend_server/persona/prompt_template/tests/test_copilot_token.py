# flake8: noqa: E402
import os
import json
import tempfile
import types

import requests

# Ensure repo path is importable
import sys
import pathlib
ROOT = str(pathlib.Path(__file__).resolve().parents[3])
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from persona.prompt_template.copilot_token import (
    resolve_copilot_api_token,
    _derive_base_url_from_token,
)


class DummyResp:
    def __init__(self, ok=True, status=200, json_body=None, text=""):
        self.ok = ok
        self.status_code = status
        self._json = json_body
        self.text = text

    def json(self):
        if isinstance(self._json, Exception):
            raise self._json
        return self._json


def test_derive_base_url_from_token():
    token = "foo=bar;proxy-ep=https://proxy.example.com;baz=1"
    assert _derive_base_url_from_token(token) == "https://api.example.com"


def test_resolve_token_fetch_and_cache(tmp_path, monkeypatch):
    cache_dir = tmp_path
    cache_file = str(cache_dir / "copilot.token.json")

    def fake_get(url, headers=None):
        return DummyResp(json_body={"token": "proxy-ep=https://proxy.test/;a=1", "expires_at": 9999999999})

    monkeypatch.setenv("COPILOT_GITHUB_TOKEN", "gh-test")
    info = resolve_copilot_api_token(github_token=None, env=os.environ, fetch_impl=types.SimpleNamespace(get=fake_get), cache_path=cache_file)
    assert "token" in info and "baseUrl" in info

    # second call should load from cache
    info2 = resolve_copilot_api_token(github_token=None, env=os.environ, fetch_impl=types.SimpleNamespace(get=lambda *a, **k: None), cache_path=cache_file)
    assert info2["source"].startswith("cache:")


def test_resolve_token_missing_github_token(monkeypatch):
    monkeypatch.delenv("COPILOT_GITHUB_TOKEN", raising=False)
    monkeypatch.delenv("GH_TOKEN", raising=False)
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)

    try:
        resolve_copilot_api_token(github_token=None, env=os.environ, fetch_impl=types.SimpleNamespace(get=lambda *a, **k: None), cache_path=None)
        assert False, "expected RuntimeError"
    except RuntimeError:
        pass
