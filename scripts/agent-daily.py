#!/usr/bin/env python3
"""Daily agent run: check inbox, queue feedback emails, notify owner when needed."""

from __future__ import annotations

import json
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

CHECK_SCRIPT = Path(__file__).resolve().parent / "check-gmail-inquiries.py"
SCRIPTS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS_DIR))
from store_api import load_store, save_store  # noqa: E402


def notify_owner(title: str, message: str) -> None:
    sys.path.insert(0, str(SCRIPTS_DIR))
    from notify import notify_owner as send
    send(title, message)


def parse_date(key: str) -> date | None:
    try:
        return datetime.strptime(key, "%Y-%m-%d").date()
    except ValueError:
        return None


def feedback_due(booking: dict, today: date) -> bool:
    if booking.get("feedbackSent"):
        return False
    end = parse_date(booking.get("endDate", ""))
    if not end:
        return False
    return today >= end + timedelta(days=2)


def run_feedback_agent(store: dict) -> list[dict]:
    today = date.today()
    due = []
    for booking in store.get("bookings", []):
        if booking.get("status") != "confirmed":
            continue
        if feedback_due(booking, today):
            due.append(booking)
            booking["feedbackSent"] = True
            booking["feedbackSentAt"] = datetime.now(timezone.utc).isoformat()
    if due:
        save_store(store)
    return due


def main() -> int:
    if CHECK_SCRIPT.exists():
        import subprocess
        subprocess.run([sys.executable, str(CHECK_SCRIPT)], check=False)

    store = load_store()
    awaiting_owner = [
        e for e in store.get("enquiries", [])
        if e.get("status") in ("new", "awaiting_owner_dates", "client_accepted", "awaiting_owner_confirm")
    ]
    for enquiry in awaiting_owner:
        client = enquiry.get("clientName") or enquiry.get("fromName") or "Client"
        if enquiry.get("status") in ("new", "awaiting_owner_dates"):
            notify_owner(
                "Pet sitting — your decision",
                f"{client}\nReply YES to send quote\nReply NO to decline",
            )
        elif enquiry.get("status") in ("client_accepted", "awaiting_owner_confirm"):
            notify_owner(
                "Client accepted quote",
                f"{client}\nReply YES to confirm booking on calendar",
            )

    due_feedback = run_feedback_agent(store)
    for booking in due_feedback:
        notify_owner(
            "Feedback email sent",
            f"Feedback request sent to {booking.get('clientName')} ({booking.get('petName')})",
        )

    print(f"Awaiting owner: {len(awaiting_owner)} | Feedback due: {len(due_feedback)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
