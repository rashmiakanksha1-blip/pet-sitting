#!/usr/bin/env python3
"""Read and write the live calendar store (Netlify Blobs via function, with local backup)."""

from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STORE_FILE = ROOT / "data" / "store.json"
ENV_FILE = Path(__file__).resolve().parent / ".env"

DEFAULT_STORE = {
    "version": 1,
    "enquiries": [],
    "bookings": [],
    "availability": {},
}


def _load_dotenv() -> None:
    if not ENV_FILE.exists():
        return
    for line in ENV_FILE.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip())


def _live_store_url() -> str:
    url = os.environ.get("LIVE_STORE_URL", "").rstrip("/")
    if url:
        return url
    config = ROOT / "config.js"
    if config.exists():
        match = re.search(r"publicBookingUrl:\s*['\"]([^'\"]+)['\"]", config.read_text())
        if match:
            base = match.group(1).rstrip("/")
            if base.endswith("availability.html"):
                base = base[: -len("availability.html")].rstrip("/")
            return f"{base}/.netlify/functions/store"
    return ""


def _write_key() -> str:
    if os.environ.get("STORE_WRITE_KEY"):
        return os.environ["STORE_WRITE_KEY"]
    config = ROOT / "config.js"
    if config.exists():
        match = re.search(r"storeWriteKey:\s*['\"]([^'\"]+)['\"]", config.read_text())
        if match:
            return match.group(1)
    return os.environ.get("STORE_AGENT_SECRET", "")


def _http_json(method: str, url: str, payload: dict | None = None, headers: dict | None = None) -> dict:
    data = None
    req_headers = {"Content-Type": "application/json"}
    if headers:
        req_headers.update(headers)
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=req_headers, method=method)
    with urllib.request.urlopen(req, timeout=30) as res:
        return json.loads(res.read().decode("utf-8"))


def load_store() -> dict:
    _load_dotenv()
    live_url = _live_store_url()
    if live_url:
        try:
            store = _http_json("GET", f"{live_url}?t=1")
            if isinstance(store, dict):
                return store
        except (urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError, TimeoutError):
            pass

    if STORE_FILE.exists():
        return json.loads(STORE_FILE.read_text())
    return json.loads(json.dumps(DEFAULT_STORE))


def save_store(store: dict) -> None:
    _load_dotenv()
    STORE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STORE_FILE.write_text(json.dumps(store, indent=2) + "\n")

    live_url = _live_store_url()
    write_key = _write_key()
    if not live_url or not write_key:
        return

    _http_json(
        "POST",
        live_url,
        payload={"store": store, "writeKey": write_key},
    )


def set_availability(date_key: str, status: str) -> dict:
    store = load_store()
    store.setdefault("availability", {})[date_key] = status
    save_store(store)
    return store


def remove_availability(date_key: str) -> dict:
    store = load_store()
    store.get("availability", {}).pop(date_key, None)
    save_store(store)
    return store
