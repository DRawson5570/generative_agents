#!/usr/bin/env python3
# Simple non-interactive helper to exchange a GitHub token for a Copilot token
# and print the result as JSON. Useful for automating token setup in CI.

import json
import os
import sys
import argparse

# Make project importable when running from repo root
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from persona.prompt_template.copilot_token import resolve_copilot_api_token


def main():
    p = argparse.ArgumentParser(description="Exchange a GitHub token for a Copilot token and cache it.")
    p.add_argument("--github-token", help="GitHub access token (optional; will read env vars if not provided)")
    args = p.parse_args()

    try:
        info = resolve_copilot_api_token(github_token=args.github_token)
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(2)

    print(json.dumps({"token": info["token"], "expiresAt": info["expiresAt"], "baseUrl": info["baseUrl"], "source": info.get("source")}))


if __name__ == "__main__":
    main()
