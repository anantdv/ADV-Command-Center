from __future__ import annotations

import re
from datetime import datetime


DATE_FORMATS = (
    "%Y-%m-%d",
    "%d/%m/%Y",
    "%d-%m-%Y",
    "%d.%m.%Y",
    "%m/%d/%Y",
    "%m-%d-%Y",
    "%d-%b-%Y",
    "%d %b %Y",
    "%d %B %Y",
    "%b %d, %Y",
    "%B %d, %Y",
)


def parse_any_date(value: str | None) -> str | None:
    if not value:
        return None
    text = str(value).strip()
    if not text or re.fullmatch(r"[A-Za-z ]{2,}", text):
        return None
    text = re.sub(r"^[^\dA-Za-z]+|[^\dA-Za-z]+$", "", text)
    text = re.sub(r"\s+", " ", text)
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(text[:30], fmt).date().isoformat()
        except ValueError:
            continue
    match = re.search(r"\b(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})\b", text)
    if match:
        day, month, year = [int(part) for part in match.groups()]
        if year < 100:
            year += 2000
        # Prefer Fiji/PNG/India-style dd/mm when ambiguous.
        if day <= 12 and month <= 12:
            day, month = day, month
        try:
            return datetime(year, month, day).date().isoformat()
        except ValueError:
            return None
    return None
