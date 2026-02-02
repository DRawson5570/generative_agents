#!/usr/bin/env python3
"""Simple script to test an Ollama local model via the configured OLLAMA_API_URL.

Usage:
  python scripts/ollama_test_generate.py "A short prompt"

Reads OLLAMA_API_URL and OLLAMA_MODEL from envvars and uses the project's
`Ollama_request` function for the call.
"""
import os
import sys

# Make package importable
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from persona.prompt_template.gpt_structure import Ollama_request


def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/ollama_test_generate.py \"Prompt text\"")
        sys.exit(2)

    prompt = sys.argv[1]
    model = os.environ.get("OLLAMA_MODEL")
    url = os.environ.get("OLLAMA_API_URL")
    if not url:
        print("Error: set OLLAMA_API_URL to your Ollama generation endpoint (eg http://localhost:11434/api/generate)")
        sys.exit(1)

    print(f"Using OLLAMA_API_URL={url} model={model}")
    out = Ollama_request(prompt, model=model, timeout=30, repeat=2)
    print("--- MODEL OUTPUT ---")
    print(out)


if __name__ == "__main__":
    main()
