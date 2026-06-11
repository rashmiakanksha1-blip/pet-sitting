"""Shared quote calculation for Pet Sitters Club."""

from __future__ import annotations

from datetime import date, timedelta

RATES = {
    "off-peak": {"visit": 13, "overnight": 25, "label": "Off-peak"},
    "peak": {"visit": 14, "overnight": 27, "label": "Peak"},
    "super-peak": {"visit": 16, "overnight": 30, "label": "Super peak"},
}
EXTRA_PET = {"visit": 5, "overnight": 8}
UK_BANK_HOLIDAYS = {
    2026: ["01-01", "04-03", "04-06", "05-04", "05-25", "08-31", "12-25", "12-26"],
}
BUSINESS_NAME = "Pet Sitters Club"
CONTACT_EMAIL = "petsittersclublondon@gmail.com"


def parse_date(s: str) -> date:
    y, m, d = map(int, s.split("-"))
    return date(y, m, d)


def date_key(d: date) -> str:
    return d.isoformat()


def is_christmas_eve_through_new_year(d: date) -> bool:
    return (d.month == 12 and d.day >= 24) or (d.month == 1 and d.day == 1)


def is_super_peak(d: date) -> bool:
    if is_christmas_eve_through_new_year(d):
        return True
    md = f"{d.month:02d}-{d.day:02d}"
    return md in UK_BANK_HOLIDAYS.get(d.year, [])


def is_peak(d: date) -> bool:
    if is_super_peak(d):
        return False
    return d.weekday() >= 5


def get_tier(d: date) -> str:
    if is_super_peak(d):
        return "super-peak"
    if is_peak(d):
        return "peak"
    return "off-peak"


def format_money(n: float) -> str:
    return f"£{int(n)}" if n == int(n) else f"£{n:.2f}"


def format_date_range(start: date, end: date) -> str:
    return f"{start.strftime('%d %b %Y')} - {end.strftime('%d %b %Y')}"


def build_line_items(start: date, end: date, service: str, extra_pets: int) -> list[dict]:
    items = []
    service_label = "Overnight stay" if service == "overnight" else "Visit"
    d = start
    while d <= end:
        tier = get_tier(d)
        rate = RATES[tier][service]
        extra = extra_pets * EXTRA_PET[service]
        subtotal = rate + extra
        items.append({
            "date": date_key(d),
            "date_label": d.strftime("%a, %d %b"),
            "tier_label": RATES[tier]["label"],
            "service_label": service_label,
            "description": f"{service_label} - {RATES[tier]['label']} rate",
            "subtotal": subtotal,
        })
        d += timedelta(days=1)
    return items


def build_quote(
    client_name: str,
    pet_type: str,
    pet_name: str,
    start: date,
    end: date,
    service: str,
    extra_pets: int = 0,
) -> dict:
    items = build_line_items(start, end, service, extra_pets)
    total = sum(i["subtotal"] for i in items)
    service_label = "overnight stay" if service == "overnight" else "daily visit"
    return {
        "client_name": client_name,
        "pet_type": pet_type,
        "pet_name": pet_name,
        "start_date": date_key(start),
        "end_date": date_key(end),
        "service": service,
        "service_label": service_label,
        "extra_pets": extra_pets,
        "line_items": items,
        "total": total,
        "date_range_label": format_date_range(start, end),
    }


def build_quote_email(quote: dict) -> str:
    lines = [
        f"  {i['date_label']}: {i['description']} - {format_money(i['subtotal'])}"
        for i in quote["line_items"]
    ]
    extra_note = ""
    if quote["extra_pets"]:
        svc = quote["service"]
        extra_note = (
            f"\n(Includes +{format_money(EXTRA_PET[svc])} per extra pet per day "
            f"for {quote['extra_pets']} extra pet{'s' if quote['extra_pets'] != 1 else ''}.)"
        )

    return "\n".join([
        f"Hi {quote['client_name']},",
        "",
        f"Thank you for your enquiry about care for {quote['pet_name']}.",
        "",
        "Good news — I'm available for those dates. Please find your quote attached as a PDF.",
        "",
        f"Pet: {quote['pet_type']} - {quote['pet_name']}",
        f"Dates: {quote['date_range_label']}",
        f"Service: {quote['service_label']}",
        f"Total: {format_money(quote['total'])}",
        "",
        "Please reply to confirm if you'd like to go ahead, and I'll reserve those dates for you.",
        "",
        "Best,",
        BUSINESS_NAME,
        CONTACT_EMAIL,
    ])
