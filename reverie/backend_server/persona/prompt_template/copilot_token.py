"""Copilot token resolver and cache helper.

Implements a small Python equivalent of OpenClaw's `resolveCopilotApiToken`:
- Exchanges a GitHub access token for a Copilot token via
  `https://api.github.com/copilot_internal/v2/token` (GET with Bearer header)
- Parses `token` and `expires_at` fields
- Derives a Copilot base API URL from `proxy-ep=...` present in the token string
- Caches token to a file and reuses until near expiry

This module is intentionally small and testable: network calls and cache path
can be injected for unit tests.
"""

from __future__ import annotations

import json
import os
import re
import time
from typing import Any, Dict, Optional

import requests

DEFAULT_COPILOT_TOKEN_URL = "https://api.github.com/copilot_internal/v2/token"
DEFAULT_COPILOT_API_BASE_URL = "https://api.individual.githubcopilot.com"


def resolve_copilot_cache_path(env: Optional[Dict[str, str]] = None) -> str:
    env = env or os.environ
    cache_dir = env.get("XDG_CACHE_HOME") or os.path.join(os.path.expanduser("~"), ".cache")
    path = os.path.join(cache_dir, "generative_agents")
    os.makedirs(path, exist_ok=True)
    return os.path.join(path, "github-copilot.token.json")


def _is_token_usable(cache: Dict[str, Any], now: Optional[int] = None) -> bool:
    # Keep a small safety margin (5 minutes)
    now = now or int(time.time() * 1000)
    if not cache or not isinstance(cache.get("token"), str) or "expiresAt" not in cache:
        return False
    return cache.get("expiresAt") - now > 5 * 60 * 1000


def _parse_token_response(value: Any) -> Dict[str, Any]:
    if not value or not isinstance(value, dict):
        raise ValueError("Unexpected response from Copilot token endpoint")

    token = value.get("token")
    expires_at = value.get("expires_at") or value.get("expiresAt")
    if not isinstance(token, str) or not token.strip():
        raise ValueError("Copilot token response missing token")

    # GitHub returns seconds since epoch; accept ms too
    if isinstance(expires_at, (int, float)):
        expires_ms = int(expires_at if expires_at > 10_000_000_000 else expires_at * 1000)
    elif isinstance(expires_at, str) and expires_at.strip():
        parsed = int(expires_at)
        expires_ms = int(parsed if parsed > 10_000_000_000 else parsed * 1000)
    else:
        raise ValueError("Copilot token response missing expires_at")

    return {"token": token, "expiresAt": expires_ms}


def _derive_base_url_from_token(token: str) -> Optional[str]:
    # token is semicolon-delimited key=value pairs; find proxy-ep
    m = re.search(r"(?:^|;)\s*proxy-ep=([^;\s]+)", token, re.IGNORECASE)
    if not m:
        return None
    proxy_ep = m.group(1)
    if not proxy_ep:
        return None
    host = re.sub(r"^https?://", "", proxy_ep)
    # convert proxy.* -> api.* (case-insensitive)
    host = re.sub(r"^proxy\.", "api.", host, flags=re.IGNORECASE)
    return f"https://{host}"


def resolve_copilot_api_token(
    github_token: Optional[str] = None,
    env: Optional[Dict[str, str]] = None,
    fetch_impl: Optional[Any] = None,
    cache_path: Optional[str] = None,
) -> Dict[str, Any]:
    """Resolve a Copilot API token and base URL, with caching.

    Returns: { token, expiresAt, source, baseUrl }
    """
    env = env or os.environ
    fetch_impl = fetch_impl or requests
    cache_path = cache_path or resolve_copilot_cache_path(env)

    # Check cache
    try:
        if os.path.exists(cache_path):
            with open(cache_path, "r", encoding="utf-8") as f:
                cached = json.load(f)
            if _is_token_usable(cached):
                base = cached.get("baseUrl") or _derive_base_url_from_token(cached["token"]) or DEFAULT_COPILOT_API_BASE_URL
                return {"token": cached["token"], "expiresAt": cached["expiresAt"], "source": f"cache:{cache_path}", "baseUrl": base}
    except Exception:
        # ignore cache errors and continue to fetch
        pass

    # Need to exchange github token
    token_to_use = github_token or env.get("COPILOT_GITHUB_TOKEN") or env.get("GH_TOKEN") or env.get("GITHUB_TOKEN")
    if not token_to_use:
        raise RuntimeError("No GitHub token available for Copilot token exchange")

    url = env.get("COPILOT_TOKEN_URL") or DEFAULT_COPILOT_TOKEN_URL
    headers = {"Accept": "application/json", "Authorization": f"Bearer {token_to_use}"}
    res = fetch_impl.get(url, headers=headers)
    if not getattr(res, "ok", True):
        # requests.Response uses res.ok; the shimbed fetch_impl in tests may not have ok; handle  status
        status = getattr(res, "status_code", None)
        raise RuntimeError(f"Copilot token exchange failed: HTTP {status}")

    data = res.json()
    parsed = _parse_token_response(data)
    base_url = _derive_base_url_from_token(parsed["token"]) or DEFAULT_COPILOT_API_BASE_URL

    payload = {"token": parsed["token"], "expiresAt": parsed["expiresAt"], "updatedAt": int(time.time() * 1000), "baseUrl": base_url}
    try:
        with open(cache_path, "w", encoding="utf-8") as f:
            json.dump(payload, f)
    except Exception:
        # ignore cache write errors
        pass

    return {"token": payload["token"], "expiresAt": payload["expiresAt"], "source": f"fetched:{url}", "baseUrl": base_url}
