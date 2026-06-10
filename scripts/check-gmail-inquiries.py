#!/usr/bin/env python3
"""Check Gmail for new pet sitting enquiries and append them to data/store.json."""

from __future__ import annotations

import email
import imaplib
import json
import os
import re
import sys
from datetime import datetime, timezone
from email.header import decode_header
from email.utils import parseaddr
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
ENV_FILE = SCRIPTS_DIR / ".env"
sys.path.insert(0, str(SCRIPTS_DIR))
from store_api import load_store, save_store  # noqa: E402

SUBJECT_HINTS = ("pet sitting", "pet sitting inquiry", "booking enquiry")


def load_env() -> dict[str, str]:
    env = {}
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            env[key.strip()] = value.strip().strip('"').strip("'")
    for key in ("GMAIL_IMAP_USER", "GMAIL_APP_PASSWORD", "BOOKING_EMAIL", "NOTIFY_EMAIL"):
        if key not in env and os.environ.get(key):
            env[key] = os.environ[key]
    return env


def decode_mime(value: str | None) -> str:
    if not value:
        return ""
    parts = decode_header(value)
    out = []
    for chunk, enc in parts:
        if isinstance(chunk, bytes):
            out.append(chunk.decode(enc or "utf-8", errors="replace"))
        else:
            out.append(chunk)
    return "".join(out)


def parse_field(body: str, labels: list[str]) -> str:
    for label in labels:
        match = re.search(rf"^{re.escape(label)}\s*:?\s*(.+)$", body, re.I | re.M)
        if match:
            return match.group(1).strip()
    return ""


def parse_inquiry(subject: str, body: str, from_header: str, message_id: str) -> dict:
    name, addr = parseaddr(from_header)
    client_name = parse_field(body, ["Your name", "Name", "Client name"]) or name or addr
    pet_name = parse_field(body, ["Pet name"])
    pet_type = parse_field(body, ["Pet type", "Pet type (dog / cat)"])
    service = parse_field(body, ["Service needed", "Service"]).lower()
    service_type = "visit" if "visit" in service else "overnight"
    dates_line = parse_field(body, ["Dates I'm interested in", "Dates", "Preferred dates"])

    start_date = ""
    end_date = ""
    iso_dates = re.findall(r"\d{4}-\d{2}-\d{2}", dates_line)
    if iso_dates:
        start_date = iso_dates[0]
        end_date = iso_dates[-1] if len(iso_dates) > 1 else iso_dates[0]

    extra_pets = 0
    extra_match = re.search(r"Number of pets\s*:?\s*(\d+)", body, re.I)
    if extra_match:
        extra_pets = max(0, int(extra_match.group(1)) - 1)

    slug = re.sub(r"[^a-zA-Z0-9]+", "-", message_id)[:80]
    return {
        "id": f"email-{slug}",
        "receivedAt": datetime.now(timezone.utc).isoformat(),
        "from": addr,
        "fromName": name or client_name,
        "subject": subject,
        "clientName": client_name,
        "petName": pet_name,
        "petType": pet_type,
        "startDate": start_date,
        "endDate": end_date,
        "serviceType": service_type,
        "extraPets": extra_pets,
        "notes": body.strip()[:2000],
        "clientEmail": addr,
        "status": "awaiting_owner_dates",
        "source": "email",
        "messageId": message_id,
    }


def notify_owner(title: str, message: str) -> None:
    from notify import notify_owner as send
    send(title, message)


def is_enquiry(subject: str, to_addrs: list[str], booking_email: str) -> bool:
    subject_l = subject.lower()
    if any(hint in subject_l for hint in SUBJECT_HINTS):
        return True
    booking_l = booking_email.lower()
    return any(booking_l in addr.lower() for addr in to_addrs)


def main() -> int:
    env = load_env()
    user = env.get("GMAIL_IMAP_USER")
    password = env.get("GMAIL_APP_PASSWORD")
    booking_email = env.get("BOOKING_EMAIL", "petsittersclublondon@gmail.com")

    if not user or not password:
        print("Missing GMAIL_IMAP_USER or GMAIL_APP_PASSWORD in scripts/.env", file=sys.stderr)
        return 1

    store = load_store()
    known_ids = {item.get("messageId") for item in store.get("enquiries", [])}
    new_items = []

    mail = imaplib.IMAP4_SSL("imap.gmail.com")
    mail.login(user, password)
    mail.select("INBOX")
    status, data = mail.search(None, "UNSEEN")
    if status != "OK":
        print("Could not search inbox", file=sys.stderr)
        return 1

    for num in data[0].split():
        status, msg_data = mail.fetch(num, "(RFC822)")
        if status != "OK":
            continue
        raw = msg_data[0][1]
        msg = email.message_from_bytes(raw)
        message_id = decode_mime(msg.get("Message-ID")) or str(num.decode())
        if message_id in known_ids:
            continue

        subject = decode_mime(msg.get("Subject"))
        from_header = decode_mime(msg.get("From"))
        to_header = decode_mime(msg.get("To", ""))
        to_addrs = [parseaddr(part.strip())[1] for part in to_header.split(",") if part.strip()]

        if not is_enquiry(subject, to_addrs, booking_email):
            continue

        body = ""
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == "text/plain":
                    payload = part.get_payload(decode=True) or b""
                    body = payload.decode(part.get_content_charset() or "utf-8", errors="replace")
                    break
        else:
            payload = msg.get_payload(decode=True) or b""
            body = payload.decode(msg.get_content_charset() or "utf-8", errors="replace")

        inquiry = parse_inquiry(subject, body, from_header, message_id)
        store.setdefault("enquiries", []).insert(0, inquiry)
        new_items.append(inquiry)
        mail.store(num, "+FLAGS", "\\Seen")

    mail.logout()
    if not new_items:
        print("No new enquiries.")
        return 0

    save_store(store)
    for item in new_items:
        dates = item.get("startDate") or "TBC"
        if item.get("endDate") and item.get("endDate") != item.get("startDate"):
            dates = f"{item['startDate']} – {item['endDate']}"
        notify_owner(
            "Pet sitting — your decision",
            (
                f"New enquiry from {item['clientName']}\n"
                f"Pet: {item.get('petType') or '—'} · {item.get('petName') or 'TBC'}\n"
                f"Dates: {dates}\n\n"
                f"Reply YES to send a quote\n"
                f"Reply NO to decline"
            ),
        )
        print(f"Added enquiry: {item['clientName']} ({item['id']})")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
