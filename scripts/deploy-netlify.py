#!/usr/bin/env python3
"""Deploy pet-sitting to Netlify (agent runs this — owner never touches Netlify)."""

from __future__ import annotations

import io
import json
import os
import re
import ssl
import sys
import urllib.error
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENV_FILE = Path(__file__).resolve().parent / ".env"

SKIP_DIRS = {".git", "node_modules", "venv", "__pycache__"}
SKIP_FILES = {".env", ".DS_Store"}


def load_env() -> dict[str, str]:
    env = {}
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            env[key.strip()] = value.strip().strip('"').strip("'")
    for key in ("NETLIFY_AUTH_TOKEN", "NETLIFY_SITE_ID"):
        if key not in env and os.environ.get(key):
            env[key] = os.environ[key]
    return env


def site_id_from_config() -> str:
    config = ROOT / "config.js"
    if not config.exists():
        return ""
    match = re.search(r"https://([^.]+)\.netlify\.app", config.read_text())
    return match.group(1) if match else ""


def build_zip() -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for path in ROOT.rglob("*"):
            if not path.is_file():
                continue
            rel = path.relative_to(ROOT)
            if any(part in SKIP_DIRS for part in rel.parts):
                continue
            if path.name in SKIP_FILES or path.suffix == ".pyc":
                continue
            zf.write(path, rel.as_posix())
    return buf.getvalue()


def api_request(method: str, url: str, token: str, data: bytes | None = None, content_type: str = "application/json") -> dict:
    headers = {"Authorization": f"Bearer {token}"}
    if data is not None:
        headers["Content-Type"] = content_type
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    ctx = ssl.create_default_context()
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=120) as res:
            return json.loads(res.read().decode("utf-8"))
    except urllib.error.HTTPError as err:
        body = err.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Netlify API {err.code}: {body}") from err


def resolve_site_id(token: str, env: dict) -> str:
    if env.get("NETLIFY_SITE_ID"):
        return env["NETLIFY_SITE_ID"]
    slug = site_id_from_config()
    if not slug:
        raise RuntimeError("Set NETLIFY_SITE_ID in scripts/.env")
    sites = api_request("GET", "https://api.netlify.com/api/v1/sites", token)
    for site in sites:
        if site.get("name") == slug or site.get("subdomain") == slug:
            return site["id"]
    raise RuntimeError(f"Could not find Netlify site for {slug}")


def main() -> int:
    env = load_env()
    token = env.get("NETLIFY_AUTH_TOKEN", "")
    if not token:
        print(
            "Add NETLIFY_AUTH_TOKEN to scripts/.env once (Netlify → User settings → Applications → Personal access tokens).\n"
            "The agent can deploy after that; you never open Netlify again.",
            file=sys.stderr,
        )
        return 1

    site_id = resolve_site_id(token, env)
    payload = build_zip()
    print(f"Uploading {len(payload) // 1024} KB to site {site_id}…")

    result = api_request(
        "POST",
        f"https://api.netlify.com/api/v1/sites/{site_id}/deploys",
        token,
        data=payload,
        content_type="application/zip",
    )

    url = result.get("ssl_url") or result.get("deploy_ssl_url") or result.get("url")
    print(f"Deploy started: {url or result.get('id')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
