#!/usr/bin/env python3
"""Call the FinNotes API while keeping FINNOTES_API_KEY out of model context."""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


DEFAULT_CREDENTIALS = Path.home() / ".finnotes" / "credentials.env"
DEFAULT_API_BASE = "https://api.finnotes.com/v1"


def _read_env_file(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        return values
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def _load_credentials(path: Path) -> tuple[str, str]:
    file_values = _read_env_file(path)
    api_key = os.environ.get("FINNOTES_API_KEY") or file_values.get("FINNOTES_API_KEY") or ""
    api_base = os.environ.get("FINNOTES_API_BASE") or file_values.get("FINNOTES_API_BASE") or DEFAULT_API_BASE
    api_key = api_key.strip()
    api_base = api_base.strip().rstrip("/")
    if not api_key:
        print(
            "FINNOTES_CREDENTIALS_MISSING: read references/create-api-key-guide.md",
            file=sys.stderr,
        )
        raise SystemExit(3)
    if not api_key.startswith("fnp_"):
        print(
            "FINNOTES_CREDENTIALS_INVALID_FORMAT: read references/create-api-key-guide.md",
            file=sys.stderr,
        )
        raise SystemExit(3)
    return api_base, api_key


def _normalise_path(path: str) -> str:
    if not path:
        raise SystemExit("API path is required.")
    if path.startswith("http://") or path.startswith("https://"):
        raise SystemExit("Pass only a /v1-relative path such as /news?range=today&type=all.")
    return path if path.startswith("/") else "/" + path


def _json_bytes(value: str | None) -> bytes | None:
    if value is None:
        return None
    try:
        parsed: Any = json.loads(value)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Invalid --json body: {exc}") from None
    return json.dumps(parsed, separators=(",", ":")).encode("utf-8")


def _looks_like_points_problem(status: int, body: str) -> bool:
    lower = body.lower()
    if "insufficient_points" in lower or "insufficient points" in lower:
        return True
    if "point balance" in lower or "not enough remaining" in lower:
        return True
    if status == 402:
        return True
    return False


def main() -> int:
    parser = argparse.ArgumentParser(description="Make a FinNotes API request.")
    parser.add_argument("method", nargs="?", default="GET", help="HTTP method, e.g. GET or POST.")
    parser.add_argument("path", nargs="?", default="/api-keys/current", help="API path under /v1.")
    parser.add_argument("--credentials", default=str(DEFAULT_CREDENTIALS), help="Path to credentials.env.")
    parser.add_argument("--json", default=None, help="JSON request body for POST/PATCH/PUT.")
    parser.add_argument("--check", action="store_true", help="Check the current key via /api-keys/current.")
    args = parser.parse_args()

    api_base, api_key = _load_credentials(Path(args.credentials).expanduser())
    method = "GET" if args.check else args.method.upper()
    path = "/api-keys/current" if args.check else _normalise_path(args.path)
    url = api_base + path
    body = _json_bytes(args.json)

    headers = {
        "Accept": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    if body is not None:
        headers["Content-Type"] = "application/json"

    request = urllib.request.Request(url, data=body, headers=headers, method=method)

    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            payload = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        error_body = exc.read().decode("utf-8", errors="replace")
        if exc.code == 401:
            print(
                "FINNOTES_KEY_REJECTED: read references/create-api-key-guide.md",
                file=sys.stderr,
            )
            if error_body:
                print(error_body)
            return 4
        if exc.code == 403:
            print(
                "FINNOTES_PERMISSION_REQUIRED: read references/create-api-key-guide.md",
                file=sys.stderr,
            )
            if error_body:
                print(error_body)
            return 4
        if args.check and exc.code == 404:
            print(
                "FINNOTES_KEY_CHECK_ENDPOINT_NOT_FOUND: read references/create-api-key-guide.md",
                file=sys.stderr,
            )
            if error_body:
                print(error_body)
            return 6
        if _looks_like_points_problem(exc.code, error_body):
            print(
                "FINNOTES_POINTS_OR_BALANCE_PROBLEM: read references/create-api-key-guide.md",
                file=sys.stderr,
            )
            if error_body:
                print(error_body)
            return 5
        if error_body:
            print(error_body)
        else:
            print(json.dumps({"status": exc.code, "error": "http_error"}))
        return 7
    except urllib.error.URLError as exc:
        print(f"FINNOTES_NETWORK_ERROR: {exc}", file=sys.stderr)
        return 8

    print(payload)
    return 0


if __name__ == "__main__":
    sys.exit(main())
