#!/usr/bin/env python3
"""Cancel bookings overlapping given dates, free calendar, print client emails."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from datetime import date, timedelta
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parent
STORE_FILE = ROOT / "data" / "store.json"

sys.path.insert(0, str(SCRIPT_DIR))
from quote_lib import BUSINESS_NAME, CONTACT_EMAIL, format_date_range, parse_date  # noqa: E402
from store_api import load_store, save_store  # noqa: E402


def each_date(start: date, end: date):
    d = start
    while d <= end:
        yield d
        d += timedelta(days=1)


def dates_overlap(b_start: date, b_end: date, c_start: date, c_end: date) -> bool:
    return b_start <= c_end and c_start <= b_end


def build_cancellation_email(booking: dict, reason: str) -> str:
    start = parse_date(booking["startDate"])
    end = parse_date(booking["endDate"])
    reason_line = f"\n{reason}\n" if reason else "\n"
    return "\n".join([
        f"Hi {booking['clientName']},",
        "",
        f"I'm sorry to let you know that your pet sitting booking for {booking['petName']} "
        f"({format_date_range(start, end)}) has been cancelled.",
        reason_line.rstrip(),
        "Those dates are now released on my calendar. If you'd like to rebook for different dates, "
        "just reply and I'll check availability.",
        "",
        "Sorry for any inconvenience.",
        "",
        "Best,",
        BUSINESS_NAME,
        CONTACT_EMAIL,
    ]).replace("\n\n\n", "\n\n")


def cancel_store(store: dict, cancel_start: date, cancel_end: date) -> list[dict]:
    cancelled = []
    bookings = store.get("bookings", [])
    availability = store.get("availability", {})

    for booking in bookings:
        if booking.get("status") != "confirmed":
            continue
        b_start = parse_date(booking["startDate"])
        b_end = parse_date(booking["endDate"])
        if not dates_overlap(b_start, b_end, cancel_start, cancel_end):
            continue
        booking["status"] = "cancelled"
        cancelled.append(booking)
        for d in each_date(b_start, b_end):
            key = d.isoformat()
            if availability.get(key) == "booked":
                del availability[key]

    store["bookings"] = bookings
    store["availability"] = availability
    return cancelled


def parse_date_arg(s: str) -> date:
    s = s.strip()
    for fmt in ("%Y-%m-%d", "%d %b %Y", "%d %B %Y", "%d/%m/%Y"):
        try:
            return parse_date(s) if fmt == "%Y-%m-%d" else __import__("datetime").datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    raise ValueError(f"Could not parse date: {s}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Cancel bookings by date range")
    parser.add_argument("--start", required=True, help="Cancel range start")
    parser.add_argument("--end", help="Cancel range end (defaults to start)")
    parser.add_argument("--reason", default="", help="Optional reason for client email")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--publish", action="store_true", help="Push store to live GitHub Pages (main)")
    args = parser.parse_args()

    cancel_start = parse_date_arg(args.start)
    cancel_end = parse_date_arg(args.end or args.start)
    if cancel_end < cancel_start:
        raise SystemExit("End date must be on or after start date")

    store = load_store()
    cancelled = cancel_store(store, cancel_start, cancel_end)

    if not cancelled:
        print(f"No confirmed bookings overlap {cancel_start} – {cancel_end}.")
        return 0

    print(f"Cancelling {len(cancelled)} booking(s) overlapping {cancel_start} – {cancel_end}:\n")
    for booking in cancelled:
        print(f"--- {booking['clientName']} / {booking['petName']} "
              f"({booking['startDate']} – {booking['endDate']}) ---")
        print(f"Subject: Booking cancelled — {booking['petName']}")
        print()
        print(build_cancellation_email(booking, args.reason))
        print()

    if args.dry_run:
        print("(Dry run — calendar not saved.)")
        return 0

    save_store(store)
    STORE_FILE.write_text(json.dumps(store, indent=2) + "\n")
    print(f"Store updated: {STORE_FILE}")

    if args.publish:
        pub = SCRIPT_DIR / "publish-store.sh"
        if pub.exists():
            subprocess.run(["bash", str(pub)], check=True)
        else:
            print("Run publish-store.sh to push live.", file=sys.stderr)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
