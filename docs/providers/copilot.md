# GitHub Copilot (integration)

This project supports using GitHub Copilot models as a backend for text generation.

Key configuration options (environment variables):

- `LLM_BACKEND`: set to `copilot` to route `ChatGPT_request`/wrappers to Copilot. Default: `openai`.
- `COPILOT_API_URL`: optional. If set, the adapter will post to this URL (proxy mode, e.g., Copilot Proxy).
- `COPILOT_GITHUB_TOKEN`, `GH_TOKEN`, or `GITHUB_TOKEN`: GitHub access token used to exchange for a Copilot API token when `COPILOT_API_URL` is not set.
- `COPILOT_DEFAULT_MODEL`: default Copilot model to use when none is provided. Default: `grok-code-fast-1`.
- `COPILOT_TOKEN_URL`: override the token exchange endpoint (defaults to `https://api.github.com/copilot_internal/v2/token`).

Usage patterns

1. Proxy mode (recommended when you already run Copilot Proxy):

```bash
export COPILOT_API_URL="http://localhost:4000/v1"
export COPILOT_DEFAULT_MODEL="grok-code-fast-1"
export LLM_BACKEND=copilot
# Now the code will call COPILOT_API_URL for generation requests
```

2. Token-exchange mode (no local proxy):

```bash
export COPILOT_GITHUB_TOKEN="<your_github_personal_or_device_flow_token>"
export LLM_BACKEND=copilot
# The app will exchange the GitHub token for a Copilot token and derive the API base URL.
```

Helper script

A small helper is included at `scripts/copilot_login.py` that accepts a GitHub token and stores the Copilot token in a cache file for later use:

```bash
python scripts/copilot_login.py --github-token <GH_TOKEN>
# Prints JSON with token, expiresAt and baseUrl and caches it at ~/.cache/generative_agents/github-copilot.token.json
```

Notes

- The adapter attempts to be permissive about API response shapes, but production Copilot integrations should verify the exact API returned by your Copilot provider (proxy or GitHub's endpoint).
- Embeddings are not implemented for Copilot in this repository; you can continue to use OpenAI embeddings or add a Copilot embedding adapter if you need them.
- Tests: unit tests mock network behavior. An integration test that exercises token exchange is included and runs only when `COPILOT_GITHUB_TOKEN` is set in the environment (so CI won't call external services by default).
