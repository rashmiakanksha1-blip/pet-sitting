#!/usr/bin/env python3
"""Send owner notifications via Telegram (preferred), email, or Mac popup."""

from __future__ import annotations

import json
import os
import subprocess
import urllib.parse
import urllib.request
from pathlib import Path

ENV_FILE = Path(__file__).resolve().parent / ".env"


def load_env() -> dict[str, str]:
    env: dict[str, str] = {}
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            env[key.strip()] = value.strip().strip('"').strip("'")
    for key in (
        "GMAIL_IMAP_USER",
        "GMAIL_APP_PASSWORD",
        "NOTIFY_EMAIL",
        "TELEGRAM_BOT_TOKEN",
        "TELEGRAM_CHAT_ID",
        "NOTIFY_CHANNEL",
    ):
        if key not in env and os.environ.get(key):
            env[key] = os.environ[key]
    return env


def notify_mac(title: str, message: str) -> bool:
    script = f'display notification {json.dumps(message)} with title {json.dumps(title)}'
    result = subprocess.run(["osascript", "-e", script], check=False)
    return result.returncode == 0


def notify_email(env: dict[str, str], subject: str, body: str) -> bool:
    notify_to = env.get("NOTIFY_EMAIL")
    user = env.get("GMAIL_IMAP_USER")
    password = env.get("GMAIL_APP_PASSWORD")
    if not notify_to or not user or not password:
        return False
    import smtplib
    from email.mime.text import MIMEText

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = user
    msg["To"] = notify_to
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(user, password)
        smtp.send_message(msg)
    return True


def notify_telegram(env: dict[str, str], title: str, message: str) -> bool:
    token = env.get("TELEGRAM_BOT_TOKEN")
    chat_id = env.get("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        return False
    text = f"*{title}*\n\n{message}"
    url = (
        f"https://api.telegram.org/bot{token}/sendMessage?"
        + urllib.parse.urlencode({
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "Markdown",
        })
    )
    req = urllib.request.Request(url, method="GET")
    with urllib.request.urlopen(req, timeout=15) as resp:
        return resp.status == 200


def notify_owner(title: str, message: str) -> None:
    """Send notification using the channel set in NOTIFY_CHANNEL (telegram | email | mac)."""
    env = load_env()
    channel = (env.get("NOTIFY_CHANNEL") or "telegram").lower()

    if channel == "telegram" and notify_telegram(env, title, message):
        return
    if channel == "email" and notify_email(env, title, message):
        return
    if channel == "mac":
        notify_mac(title, message)
        return

    # Fallback chain: try all available methods
    if notify_telegram(env, title, message):
        return
    if notify_email(env, title, message):
        return
    notify_mac(title, message)
