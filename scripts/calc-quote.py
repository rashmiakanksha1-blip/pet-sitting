#!/usr/bin/env python3
"""Calculate a pet sitting quote and print a ready-to-send client email."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from quote_lib import build_quote, build_quote_email, parse_date

SCRIPT_DIR = Path(__file__).resolve().parent


def main() -> int:
    parser = argparse.ArgumentParser(description="Calculate quote and print client email")
    parser.add_argument("--client", required=True)
    parser.add_argument("--pet-type", required=True, help="Cat or Dog")
    parser.add_argument("--pet-name", required=True)
    parser.add_argument("--start", required=True, help="YYYY-MM-DD")
    parser.add_argument("--end", required=True, help="YYYY-MM-DD")
    parser.add_argument("--service", choices=["overnight", "visit"], default="overnight")
    parser.add_argument("--extra-pets", type=int, default=0)
    parser.add_argument("--subject-only", action="store_true")
    parser.add_argument("--pdf", action="store_true", help="Also generate PDF receipt")
    args = parser.parse_args()

    start = parse_date(args.start)
    end = parse_date(args.end)
    if end < start:
        raise SystemExit("End date must be on or after start date")

    if args.subject_only:
        print(f"Your pet sitting quote — {args.client}")
        return 0

    if args.pdf:
        py = SCRIPT_DIR / "venv" / "bin" / "python"
        if not py.exists():
            py = Path(sys.executable)
        cmd = [
            str(py), str(SCRIPT_DIR / "generate-receipt-pdf.py"),
            "--client", args.client,
            "--pet-type", args.pet_type,
            "--pet-name", args.pet_name,
            "--start", args.start,
            "--end", args.end,
            "--service", args.service,
            "--extra-pets", str(args.extra_pets),
        ]
        return subprocess.call(cmd)

    quote = build_quote(
        args.client, args.pet_type, args.pet_name,
        start, end, args.service, args.extra_pets,
    )
    print(build_quote_email(quote))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
