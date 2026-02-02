# flake8: noqa: E402
import os
import pytest

# Ensure project path for imports
import sys
import pathlib
ROOT = str(pathlib.Path(__file__).resolve().parents[3])
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from persona.prompt_template.copilot_token import resolve_copilot_api_token


@pytest.mark.skipif("COPILOT_GITHUB_TOKEN" not in os.environ, reason="No COPILOT_GITHUB_TOKEN set; skip integration test")
def test_resolve_copilot_token_integration():
    # This is a gated integration test; it actually hits the Copilot token endpoint.
    info = resolve_copilot_api_token()
    assert "token" in info and info.get("baseUrl")


@pytest.mark.skipif("COPILOT_GITHUB_TOKEN" not in os.environ, reason="No COPILOT_GITHUB_TOKEN set; skip integration test")
def test_copilot_request_smoke(monkeypatch):
    # If you have a real token + actual Copilot service, this would make a generation request.
    # We keep this as a gated smoke test; it won't run in CI unless you set COPILOT_GITHUB_TOKEN.
    from persona.prompt_template.gpt_structure import Copilot_request

    # Do not assert on actual content; just ensure the call executes without raising.
    _ = Copilot_request("Hello from integration test", model=None)
    assert True
