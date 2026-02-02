# flake8: noqa: E402
import os
import pytest

# Ensure repo in path
import sys
import pathlib
ROOT = str(pathlib.Path(__file__).resolve().parents[3])
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from persona.prompt_template.gpt_structure import Ollama_request


@pytest.mark.skipif("OLLAMA_API_URL" not in os.environ, reason="No OLLAMA_API_URL set; skip local ollama integration test")
def test_ollama_local_smoke():
    model = os.environ.get("OLLAMA_MODEL")

    out = Ollama_request("Say hello in one word", model=model, timeout=30, repeat=2)
    assert out is not None
    assert isinstance(out, str)
    assert len(out.strip()) > 0
