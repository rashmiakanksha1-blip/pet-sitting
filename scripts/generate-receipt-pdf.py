#!/usr/bin/env python3
"""Generate a client quote receipt PDF and a short email to attach it."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from datetime import date
from pathlib import Path

from fpdf import FPDF

from brand import (
    ACCENT,
    ACCENT_DARK,
    ACCENT_LIGHT_SOFT,
    ACCENT_MID,
    PAGE_BG,
    PAGE_BG_WARM,
    PAGE_TEXT,
    PAGE_TEXT_MUTED,
    PANEL_BORDER,
    SAGE_DARK,
    SAGE_HUE,
    SAGE_LIGHT,
    WHITE,
)
from quote_lib import (
    BUSINESS_NAME,
    CONTACT_EMAIL,
    build_quote,
    build_quote_email,
    format_money,
    parse_date,
)

ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "receipts" / "output"
COUNTER_FILE = ROOT / "data" / "receipt-counter.json"
LOGO_PATH = ROOT / "assets" / "logo-icon.png"
SCRIPT_DIR = Path(__file__).resolve().parent


def ensure_logo() -> Path:
    if not LOGO_PATH.exists():
        py = SCRIPT_DIR / "venv" / "bin" / "python"
        if not py.exists():
            py = Path(sys.executable)
        subprocess.run([str(py), str(SCRIPT_DIR / "build_logo.py")], check=True)
    return LOGO_PATH


def next_receipt_number() -> str:
    COUNTER_FILE.parent.mkdir(parents=True, exist_ok=True)
    counter = 1
    if COUNTER_FILE.exists():
        try:
            counter = int(json.loads(COUNTER_FILE.read_text()).get("next", 1))
        except (json.JSONDecodeError, ValueError):
            counter = 1
    number = f"PS-{counter:04d}"
    COUNTER_FILE.write_text(json.dumps({"next": counter + 1}, indent=2) + "\n")
    return number


def slugify(*parts: str) -> str:
    raw = "-".join(parts).lower()
    return re.sub(r"[^a-z0-9]+", "-", raw).strip("-")[:60]


class ReceiptPDF(FPDF):
    def header(self):
        pass

    def footer(self):
        self.set_y(-18)
        self.set_font("Helvetica", "", 8)
        self.set_text_color(*PAGE_TEXT_MUTED)
        self.cell(0, 5, f"Thank you for trusting {BUSINESS_NAME} with your pet!", align="C")
        self.ln(4)
        self.cell(0, 5, f"Questions? Email {CONTACT_EMAIL}", align="C")


def _lerp_color(a: tuple[int, int, int], b: tuple[int, int, int], t: float) -> tuple[int, int, int]:
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def _gradient_rect(
    pdf: FPDF,
    x: float,
    y: float,
    w: float,
    h: float,
    top: tuple[int, int, int],
    mid: tuple[int, int, int],
    bottom: tuple[int, int, int],
    steps: int = 30,
) -> None:
    """Approximate the site hero terracotta gradient (160deg)."""
    for i in range(steps):
        t = i / max(steps - 1, 1)
        color = _lerp_color(top, mid, t * 1.4) if t < 0.55 else _lerp_color(mid, bottom, (t - 0.55) / 0.45)
        strip_h = h / steps + 0.2
        pdf.set_fill_color(*color)
        pdf.rect(x, y + i * (h / steps), w, strip_h, style="F")


def _truncate(pdf: FPDF, text: str, max_w: float) -> str:
    if pdf.get_string_width(text) <= max_w:
        return text
    ellipsis = "..."
    while text and pdf.get_string_width(text + ellipsis) > max_w:
        text = text[:-1]
    return (text + ellipsis) if text else ellipsis


def _fit_cell(pdf: FPDF, w: float, h: float, text: str, **kwargs) -> None:
    pad = 2
    pdf.cell(w, h, _truncate(pdf, text, w - pad), **kwargs)


def render_pdf(quote: dict, receipt_number: str, issued: date) -> bytes:
    logo = ensure_logo()
    pdf = ReceiptPDF()
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.add_page()

    margin = 18
    content_w = 210 - margin * 2
    logo_mm = 14
    text_x = margin + logo_mm + 4
    brand_w = 88
    right_w = content_w - brand_w - 6
    right_x = margin + brand_w + 6
    header_h = 48

    pdf.set_margins(margin, margin, margin)

    # Cream page background (site --page-bg)
    pdf.set_fill_color(*PAGE_BG)
    pdf.rect(0, header_h, 210, 297 - header_h, style="F")

    # Terracotta hero ribbon + site logo
    _gradient_rect(pdf, 0, 0, 210, header_h, ACCENT_DARK, ACCENT, ACCENT_MID)

    pdf.image(str(logo), x=margin, y=9, w=logo_mm, h=logo_mm)

    pdf.set_xy(text_x, 11)
    pdf.set_font("Helvetica", "B", 18)
    pdf.set_text_color(*WHITE)
    pdf.cell(brand_w - logo_mm - 4, 8, BUSINESS_NAME)
    pdf.ln(8)
    pdf.set_x(text_x)
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(250, 244, 240)
    pdf.cell(brand_w - logo_mm - 4, 5, "Pet sitting services")
    pdf.ln(5)
    pdf.set_x(text_x)
    pdf.set_font("Helvetica", "", 8)
    pdf.cell(brand_w - logo_mm - 4, 4, CONTACT_EMAIL)

    issued_label = issued.strftime("%d %b %Y")
    pdf.set_xy(right_x, 11)
    pdf.set_font("Helvetica", "B", 13)
    pdf.set_text_color(*WHITE)
    pdf.cell(right_w, 7, "QUOTE", align="R")
    pdf.ln(7)
    pdf.set_x(right_x)
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(250, 244, 240)
    pdf.cell(right_w, 5, receipt_number, align="R")
    pdf.ln(5)
    pdf.set_x(right_x)
    pdf.cell(right_w, 5, f"Issued {issued_label}", align="R")
    pdf.ln(5)
    pdf.set_x(right_x)
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_text_color(*WHITE)
    pdf.cell(right_w, 5, "Payment pending", align="R")

    pdf.set_y(header_h + 10)
    pdf.set_text_color(*PAGE_TEXT)

    # Bill to — accent-light-soft panel (site rate cards)
    pdf.set_font("Helvetica", "B", 8)
    pdf.set_text_color(*PAGE_TEXT_MUTED)
    pdf.cell(0, 6, "BILL TO")
    pdf.ln(7)
    bill_lines = [
        quote["client_name"],
        f"Pet: {quote['pet_type']} - {quote['pet_name']}",
        f"Dates: {quote['date_range_label']}",
        f"Service: {quote['service_label'].title()}",
    ]
    bill_h = 10 + len(bill_lines) * 6
    box_y = pdf.get_y()
    pdf.set_fill_color(*ACCENT_LIGHT_SOFT)
    pdf.set_draw_color(*PANEL_BORDER)
    pdf.rect(margin, box_y, content_w, bill_h, style="DF")
    pdf.set_xy(margin + 6, box_y + 5)
    pdf.set_font("Helvetica", "B", 12)
    pdf.set_text_color(*PAGE_TEXT)
    pdf.cell(content_w - 12, 7, bill_lines[0])
    pdf.ln(7)
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(*PAGE_TEXT_MUTED)
    for line in bill_lines[1:]:
        pdf.set_x(margin + 6)
        pdf.cell(content_w - 12, 5, line)
        pdf.ln(5)

    pdf.set_y(box_y + bill_h + 8)

    # Table — sage-hue header (site calendar ribbon)
    col_w = (52, 90, 32)
    row_h = 8

    pdf.set_fill_color(*SAGE_HUE)
    pdf.set_text_color(*WHITE)
    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(col_w[0], 9, "Date", border=0, fill=True)
    pdf.cell(col_w[1], 9, "Description", border=0, fill=True)
    pdf.cell(col_w[2], 9, "Amount", border=0, fill=True, align="R")
    pdf.ln(9)

    pdf.set_font("Helvetica", "", 8)
    pdf.set_text_color(*PAGE_TEXT)
    for i, item in enumerate(quote["line_items"]):
        pdf.set_fill_color(*(WHITE if i % 2 == 0 else PAGE_BG_WARM))
        desc = f"{item['service_label']} ({item['tier_label']})"
        _fit_cell(pdf, col_w[0], row_h, item["date_label"], border=0, fill=True)
        _fit_cell(pdf, col_w[1], row_h, desc, border=0, fill=True)
        _fit_cell(pdf, col_w[2], row_h, format_money(item["subtotal"]), border=0, fill=True, align="R")
        pdf.ln(row_h)

    # Total — sage-light (site calendar accents)
    pdf.ln(4)
    pdf.set_fill_color(*SAGE_LIGHT)
    pdf.set_draw_color(*SAGE_HUE)
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(*SAGE_DARK)
    pdf.cell(col_w[0] + col_w[1], 12, "Total due", border=0, fill=True)
    pdf.cell(col_w[2], 12, format_money(quote["total"]), border=0, fill=True, align="R")
    pdf.ln(14)

    pdf.set_font("Helvetica", "I", 9)
    pdf.set_text_color(*PAGE_TEXT_MUTED)
    pdf.multi_cell(
        0, 5,
        "This quote is valid pending your confirmation. Dates will be reserved once you reply to accept.",
    )

    return pdf.output()


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate quote receipt PDF + email text")
    parser.add_argument("--client", required=True)
    parser.add_argument("--pet-type", required=True)
    parser.add_argument("--pet-name", required=True)
    parser.add_argument("--start", required=True, help="YYYY-MM-DD")
    parser.add_argument("--end", required=True, help="YYYY-MM-DD")
    parser.add_argument("--service", choices=["overnight", "visit"], default="overnight")
    parser.add_argument("--extra-pets", type=int, default=0)
    parser.add_argument("--email-only", action="store_true")
    parser.add_argument("--pdf-only", action="store_true")
    args = parser.parse_args()

    start = parse_date(args.start)
    end = parse_date(args.end)
    if end < start:
        raise SystemExit("End date must be on or after start date")

    quote = build_quote(
        args.client, args.pet_type, args.pet_name,
        start, end, args.service, args.extra_pets,
    )
    receipt_number = next_receipt_number()
    issued = date.today()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    filename = f"{receipt_number}-{slugify(args.client, args.pet_name)}.pdf"
    pdf_path = OUTPUT_DIR / filename

    if not args.email_only:
        pdf_path.write_bytes(render_pdf(quote, receipt_number, issued))

    if not args.pdf_only:
        print(f"Subject: Your pet sitting quote — {args.client}")
        print()
        print(build_quote_email(quote))

    if not args.email_only:
        print()
        print(f"PDF saved: {pdf_path}")
        print(f"Receipt: {receipt_number}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
