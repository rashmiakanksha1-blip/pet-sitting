#!/usr/bin/env python3
"""Update the live calendar — run this when the owner asks for a change in chat."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from store_api import STORE_FILE, load_store, remove_availability, save_store, set_availability


def main() -> int:
    parser = argparse.ArgumentParser(description="Update Pet Sitters Club live calendar")
    sub = parser.add_subparsers(dest="command", required=True)

    avail = sub.add_parser("availability", help="Set a day to available, booked, or unavailable")
    avail.add_argument("date", help="Date as YYYY-MM-DD")
    avail.add_argument("status", choices=["available", "booked", "unavailable"])

    sub.add_parser("push", help="Upload data/store.json to the live store")

    show = sub.add_parser("show", help="Print current store")

    args = parser.parse_args()

    if args.command == "availability":
        if args.status == "available":
            store = remove_availability(args.date)
        else:
            store = set_availability(args.date, args.status)
        print(f"Updated {args.date} → {args.status}")
        print(f"Live sync: {'yes' if _live_configured() else 'local file only (set LIVE_STORE_URL in scripts/.env)'}")
        return 0

    if args.command == "push":
        import json
        store = json.loads(STORE_FILE.read_text()) if STORE_FILE.exists() else load_store()
        save_store(store)
        print("Store pushed to live.")
        return 0

    if args.command == "show":
        import json
        print(json.dumps(load_store(), indent=2))
        return 0

    return 1


def _live_configured() -> bool:
    import os
    from store_api import ENV_FILE
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text().splitlines():
            if line.startswith("LIVE_STORE_URL=") and line.split("=", 1)[1].strip():
                return True
    return bool(os.environ.get("LIVE_STORE_URL"))


if __name__ == "__main__":
    raise SystemExit(main())
