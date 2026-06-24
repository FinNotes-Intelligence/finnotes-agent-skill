#!/usr/bin/env python3
"""Delete a downloaded FinNotes handoff JSON after explicit user confirmation."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


def _load_metadata(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        print(f"FinNotes handoff JSON already missing: {path}")
        raise SystemExit(0) from None
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Refusing to delete non-JSON file: {exc}") from None


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Delete a FinNotes Agent JSON handoff after import."
    )
    parser.add_argument("--handoff", required=True, help="Downloaded FinNotes Agent JSON path.")
    parser.add_argument(
        "--confirmed",
        action="store_true",
        help="Required. Pass only after the user explicitly confirms deletion.",
    )
    args = parser.parse_args()

    if not args.confirmed:
        raise SystemExit("Refusing to delete without --confirmed.")

    handoff_path = Path(args.handoff).expanduser()
    handoff = _load_metadata(handoff_path)

    if handoff.get("kind") != "finnotes.agent_key_handoff" or handoff.get("version") != 1:
        raise SystemExit("Refusing to delete: unsupported FinNotes handoff format.")

    handoff_path.unlink()
    print(f"Deleted FinNotes handoff JSON: {handoff_path}")
    print("Stored secret and public metadata remain in ~/.finnotes/.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
