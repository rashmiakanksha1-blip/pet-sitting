#!/usr/bin/env python3
"""Print your Telegram chat id after you have messaged your bot."""

from __future__ import annotations

import json
import os
import sys
import urllib.request
from pathlib import Path

ENV_FILE = Path(__file__).resolve().parent / ".env"


def load_token() -> str:
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text().splitlines():
            if line.strip().startswith("TELEGRAM_BOT_TOKEN="):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    return os.environ.get("TELEGRAM_BOT_TOKEN", "")


def main() -> int:
    token = load_token()
    if not token:
        print("Add TELEGRAM_BOT_TOKEN to scripts/.env first.", file=sys.stderr)
        return 1
    url = f"https://api.telegram.org/bot{token}/getUpdates"
    with urllib.request.urlopen(url, timeout=15) as resp:
        data = json.loads(resp.read().decode())
    updates = data.get("result", [])
    if not updates:
        print("No messages yet. Open Telegram, find your bot, tap Start, send any message, then run this again.")
        return 1
    chat_ids = []
    for item in updates:
        msg = item.get("message") or item.get("edited_message") or {}
        chat = msg.get("chat") or {}
        cid = chat.get("id")
        name = chat.get("first_name") or chat.get("username") or "you"
        if cid and cid not in chat_ids:
            chat_ids.append(cid)
            print(f"TELEGRAM_CHAT_ID={cid}  ({name})")
    print("\nCopy the chat id into scripts/.env")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
