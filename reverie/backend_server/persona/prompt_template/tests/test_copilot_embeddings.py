# flake8: noqa: E402
import types

# ensure repo imports
import sys
import pathlib
ROOT = str(pathlib.Path(__file__).resolve().parents[3])
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import persona.prompt_template.gpt_structure as gs


class DummyResp:
    def __init__(self, status=200, json_body=None):
        self._status = status
        self._json = json_body

    def raise_for_status(self):
        if self._status >= 400:
            raise Exception("http")

    def json(self):
        return self._json


def test_copilot_embeddings_via_custom_url(monkeypatch):
    def fake_resolve():
        return {"token": "t", "baseUrl": "http://api.test"}

    def fake_post(url, json, headers, timeout):
        assert headers["Authorization"] == "Bearer t"
        return DummyResp(json_body={"data": [{"embedding": [1, 2, 3]}]})

    monkeypatch.setenv("COPILOT_EMBEDDINGS_URL", "http://emb.test/v1/embeddings")
    monkeypatch.setattr(gs, "resolve_copilot_api_token", fake_resolve)
    monkeypatch.setattr(gs.requests, "post", fake_post)

    emb = gs.Copilot_get_embedding("hello")
    assert emb == [1, 2, 3]


def test_copilot_embeddings_fallback_to_openai(monkeypatch):
    # force both Copilot calls to fail, ensure we call openai.Embedding.create
    def fake_resolve():
        return {"token": "t", "baseUrl": "http://api.test"}

    def fake_post_fail(*a, **k):
        raise Exception("nope")

    monkeypatch.setattr(gs, "resolve_copilot_api_token", fake_resolve)
    monkeypatch.setattr(gs.requests, "post", fake_post_fail)

    class FakeEmb:
        @staticmethod
        def create(input, model):
            return {"data": [{"embedding": [9, 9, 9]}]}

    monkeypatch.setattr(gs.openai, "Embedding", FakeEmb)

    emb = gs.Copilot_get_embedding("hello")
    assert emb == [9, 9, 9]
