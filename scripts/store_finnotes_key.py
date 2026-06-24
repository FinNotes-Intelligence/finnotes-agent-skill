#!/usr/bin/env python3
"""Import a FinNotes Agent JSON handoff without printing the API key."""

from __future__ import annotations

import argparse
import json
import os
import stat
import sys
from pathlib import Path
from typing import Any


DEFAULT_DIR = Path.home() / ".finnotes"
DEFAULT_CREDENTIALS = DEFAULT_DIR / "credentials.env"
DEFAULT_PROFILE = DEFAULT_DIR / "profile.json"


def _expand(value: str | None, fallback: Path) -> Path:
    if not value:
        return fallback
    return Path(value).expanduser()


def _write_private_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    try:
        os.chmod(tmp, stat.S_IRUSR | stat.S_IWUSR)
    except OSError:
        pass
    tmp.replace(path)
    try:
        os.chmod(path, stat.S_IRUSR | stat.S_IWUSR)
    except OSError:
        pass


def _load_handoff(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise SystemExit(f"FinNotes handoff JSON not found: {path}") from None
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Invalid FinNotes handoff JSON: {exc}") from None


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Store a downloaded FinNotes Agent JSON handoff locally."
    )
    parser.add_argument("--handoff", required=True, help="Downloaded FinNotes Agent JSON path.")
    parser.add_argument("--profile", default=None, help="Override profile name written to metadata.")
    args = parser.parse_args()

    handoff_path = Path(args.handoff).expanduser()
    handoff = _load_handoff(handoff_path)

    if handoff.get("kind") != "finnotes.agent_key_handoff" or handoff.get("version") != 1:
        raise SystemExit("Unsupported FinNotes handoff format.")

    credential = handoff.get("credential") or {}
    api = handoff.get("api") or {}
    storage = handoff.get("storage") or {}
    key_metadata = handoff.get("key_metadata") or {}

    api_key = str(credential.get("plaintext") or "").strip()
    if not api_key.startswith("fnp_"):
        raise SystemExit("Handoff does not contain a valid fnp_ API key.")

    credential_type = str(credential.get("type") or "bearer").strip().lower()
    if credential_type != "bearer":
        raise SystemExit("Unsupported FinNotes credential type.")

    env_name = str(credential.get("env_name") or "FINNOTES_API_KEY").strip()
    if env_name != "FINNOTES_API_KEY":
        raise SystemExit("Unsupported FinNotes credential env_name.")

    api_base = str(api.get("base_url") or "https://api.finnotes.com/v1").rstrip("/")
    profile_name = args.profile or "default"

    credentials_path = _expand(storage.get("credentials_env"), DEFAULT_CREDENTIALS)
    profile_path = _expand(storage.get("profile_json"), DEFAULT_PROFILE)

    credentials_body = (
        f"FINNOTES_API_BASE={api_base}\n"
        f"FINNOTES_API_KEY={api_key}\n"
    )
    _write_private_text(credentials_path, credentials_body)

    metadata = {
        "profile": profile_name,
        "api_base": api_base,
        "handoff_issued_at": handoff.get("issued_at"),
        "source": handoff.get("source") or {},
        "credential_env_name": env_name,
        "key_name": key_metadata.get("name"),
        "key_prefix": key_metadata.get("prefix") or credential.get("display_prefix"),
        "plan": key_metadata.get("plan"),
        "created_at": key_metadata.get("created_at"),
        "imported_from": str(handoff_path),
        "permissions": key_metadata.get("permissions") or {},
        "secret_storage": str(credentials_path),
    }
    profile_path.parent.mkdir(parents=True, exist_ok=True)
    profile_path.write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    enabled = ", ".join(k for k, v in metadata["permissions"].items() if v) or "none"
    print(f"Imported FinNotes profile: {profile_name}")
    print(f"Key: {metadata.get('key_prefix') or 'fnp_********'}...")
    print(f"Permissions: {enabled}")
    print(f"Secret stored in: {credentials_path}")
    print(f"Metadata stored in: {profile_path}")
    print("Public metadata command: python scripts/finnotes_profile.py")
    print(f"Handoff JSON still exists: {handoff_path}")
    print("After confirming with the user, delete it with: python scripts/delete_finnotes_handoff.py --handoff <path> --confirmed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
