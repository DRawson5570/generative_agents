# Ollama (local models)

This project supports using Ollama as a local LLM backend. Ollama can host local models (7B/8B variants) that you can run on your machine or a server; this guide helps you configure and test a local model.

Prerequisites

- Install Ollama by following the official Ollama installation instructions for your platform.
- Acquire or pull a local 7B/8B model that Ollama supports (for example a Llama- or Mistral-based 7B model). The exact model name varies by distribution; use `ollama pull <model>` or the Ollama UI.

Configuration

Set these environment variables in your shell (example values):

```bash
export LLM_BACKEND=ollama
export OLLAMA_API_URL="http://localhost:11434/api/generate"  # change if your Ollama host is different
export OLLAMA_MODEL="<your-local-model-name>"                # e.g., llama2-7b or mistral-7b (model names vary)
```

Notes:
- Ollama may serve different HTTP endpoints depending on the version; `OLLAMA_API_URL` should be the URL you use to send generation requests.
- Running a 7B/8B model locally may require GPUs or a beefy CPU; check your model requirements.

Testing locally

A small convenience script helps you sanity-check a model:

```bash
python scripts/ollama_test_generate.py "Write a one-line summary: The quick brown fox"
```

This script reads `OLLAMA_API_URL` and `OLLAMA_MODEL` from the environment and prints the model output.

Gated integration test

The test `reverie/backend_server/persona/prompt_template/tests/test_ollama_local_integration.py` is provided and will only run if `OLLAMA_API_URL` is set. Use it to validate a local model in your development environment.

If you want, I can add more automation (pulling models via `ollama pull`, launching `ollama serve`, or adding systemd unit examples). Tell me which of those you prefer.