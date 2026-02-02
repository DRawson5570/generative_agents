#!/usr/bin/env python3
"""Interactive GitHub device-flow helper to obtain a GitHub access token and
automatically exchange it for a Copilot token using `resolve_copilot_api_token`.

This mirrors OpenClaw's `openclaw models auth login-github-copilot` behavior
but in a lightweight script suitable for local usage.

Usage:
  python scripts/copilot_device_login.py
"""

import sys
import time
import json
import os
import requests

GITHUB_DEVICE_CODE_URL = "https://github.com/login/device/code"
GITHUB_ACCESS_TOKEN_URL = "https://github.com/login/oauth/access_token"
CLIENT_ID = os.environ.get("COPILOT_GITHUB_CLIENT_ID", "Iv1.b507a08c87ecfe98")

# make local importable
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from persona.prompt_template.copilot_token import resolve_copilot_api_token


def request_device_code(scope: str = "read:user"):
    body = {"client_id": CLIENT_ID, "scope": scope}
    res = requests.post(GITHUB_DEVICE_CODE_URL, data=body, headers={"Accept": "application/json"})
    res.raise_for_status()
    return res.json()


def poll_for_access_token(device_code: str, interval: int, expires_in: int):
    deadline = time.time() + expires_in
    while time.time() < deadline:
        body = {
            "client_id": CLIENT_ID,
            "device_code": device_code,
            "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
        }
        res = requests.post(GITHUB_ACCESS_TOKEN_URL, data=body, headers={"Accept": "application/json"})
        res.raise_for_status()
        data = res.json()
        if "access_token" in data and data["access_token"]:
            return data["access_token"]
        err = data.get("error")
        if err == "authorization_pending":
            time.sleep(interval)
            continue
        if err == "slow_down":
            interval += 5
            time.sleep(interval)
            continue
        if err == "expired_token":
            raise RuntimeError("Device code expired; run again")
        if err == "access_denied":
            raise RuntimeError("Authorization denied")
        raise RuntimeError(f"Device flow error: {err}")
    raise RuntimeError("Device flow timed out")


def main():
    print("Requesting device code from GitHub...")
    device = request_device_code()
    print("Visit:", device["verification_uri"])
    print("Code:", device["user_code"])
    print("Waiting for authorization...")

    try:
        token = poll_for_access_token(device["device_code"], device["interval"], device["expires_in"])
    except Exception as e:
        print("ERROR:", e)
        sys.exit(1)

    print("GitHub access token acquired")
    # exchange for Copilot token and cache
    info = resolve_copilot_api_token(github_token=token)
    print("Copilot token fetched and cached:")
    print(json.dumps(info, indent=2))


if __name__ == "__main__":
    main()
