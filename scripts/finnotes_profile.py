#!/usr/bin/env python3
"""Show non-secret FinNotes key metadata for planning and diagnostics."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


DEFAULT_PROFILE = Path.home() / ".finnotes" / "profile.json"

PERMISSION_LABELS = {
    "basic": "Basic(all news, report & data)",
    "notes": "Notes Download & Upload",
    "usage": "View usage & remaining points",
    "view_log": "View log",
    "manage_log": "Manage log",
    "manage_newsletter": "Manage newsletter preferences",
    "all_usage_state": "All-key usage state",
    "notification_management": "Notification management",
}


def _load_profile(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        print(
            "FINNOTES_PROFILE_MISSING: read references/create-api-key-guide.md",
            file=sys.stderr,
        )
        raise SystemExit(3) from None
    except json.JSONDecodeError as exc:
        print(
            f"FINNOTES_PROFILE_INVALID: {exc}; read references/create-api-key-guide.md",
            file=sys.stderr,
        )
        raise SystemExit(3) from None


def _safe_summary(profile: dict[str, Any]) -> dict[str, Any]:
    permissions = profile.get("permissions") if isinstance(profile.get("permissions"), dict) else {}
    return {
        "profile": profile.get("profile"),
        "api_base": profile.get("api_base"),
        "key_name": profile.get("key_name"),
        "key_prefix": profile.get("key_prefix"),
        "plan": profile.get("plan"),
        "created_at": profile.get("created_at"),
        "handoff_issued_at": profile.get("handoff_issued_at"),
        "permissions": {k: bool(permissions.get(k, False)) for k in PERMISSION_LABELS},
    }


def _print_text(summary: dict[str, Any]) -> None:
    permissions = summary["permissions"]
    enabled = [k for k, value in permissions.items() if value]
    disabled = [k for k, value in permissions.items() if not value]

    print(f"Profile: {summary.get('profile') or 'default'}")
    print(f"API base: {summary.get('api_base') or 'https://api.finnotes.com/v1'}")
    print(f"Key name: {summary.get('key_name') or '(unknown)'}")
    print(f"Key prefix: {summary.get('key_prefix') or '(unknown)'}")
    print(f"Plan: {summary.get('plan') or '(unknown)'}")
    print(f"Created at: {summary.get('created_at') or '(unknown)'}")
    print(f"Handoff issued at: {summary.get('handoff_issued_at') or '(unknown)'}")
    print("Permissions enabled: " + (", ".join(enabled) if enabled else "none"))
    print("Permissions disabled: " + (", ".join(disabled) if disabled else "none"))


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Print non-secret FinNotes key metadata from ~/.finnotes/profile.json."
    )
    parser.add_argument("--profile-file", default=str(DEFAULT_PROFILE), help="Path to profile.json.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    parser.add_argument(
        "--require",
        choices=sorted(PERMISSION_LABELS),
        help="Exit nonzero if the key metadata does not show this permission enabled.",
    )
    args = parser.parse_args()

    profile = _load_profile(Path(args.profile_file).expanduser())
    summary = _safe_summary(profile)

    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        _print_text(summary)

    if args.require:
        has_permission = bool(summary["permissions"].get(args.require, False))
        if not has_permission:
            label = PERMISSION_LABELS[args.require]
            print(
                f"FINNOTES_PERMISSION_MISSING: {args.require} ({label}); "
                "read references/create-api-key-guide.md",
                file=sys.stderr,
            )
            return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
