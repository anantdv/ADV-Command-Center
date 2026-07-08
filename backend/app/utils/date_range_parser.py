from __future__ import annotations

import re
from calendar import monthrange
from datetime import date, timedelta

MONTHS = {
    "jan": 1, "january": 1,
    "feb": 2, "february": 2,
    "mar": 3, "march": 3,
    "apr": 4, "april": 4,
    "may": 5,
    "jun": 6, "june": 6,
    "jul": 7, "july": 7,
    "aug": 8, "august": 8,
    "sep": 9, "sept": 9, "september": 9,
    "oct": 10, "october": 10,
    "nov": 11, "november": 11,
    "dec": 12, "december": 12,
}


def parse_month_year(text: str) -> dict[str, str] | None:
    match = re.search(r"\b(" + "|".join(MONTHS) + r")\s+(\d{4})\b", text.lower())
    if not match:
        return None
    month = MONTHS[match.group(1)]
    year = int(match.group(2))
    return _month_range(year, month)


def parse_date_range_phrase(text: str, current_date: date | None = None) -> dict[str, str] | None:
    today = current_date or date.today()
    normalized = " ".join(text.lower().split())
    if re.search(r"\btoday\b", normalized):
        return {"from_date": today.isoformat(), "to_date": today.isoformat()}
    if re.search(r"\byesterday\b", normalized):
        yesterday = today - timedelta(days=1)
        return {"from_date": yesterday.isoformat(), "to_date": yesterday.isoformat()}
    if "this month" in normalized:
        return _month_range(today.year, today.month)
    if "last month" in normalized:
        first = today.replace(day=1)
        previous = first - timedelta(days=1)
        return _month_range(previous.year, previous.month)
    if "this year" in normalized:
        return {"from_date": date(today.year, 1, 1).isoformat(), "to_date": date(today.year, 12, 31).isoformat()}
    if "last year" in normalized:
        return {"from_date": date(today.year - 1, 1, 1).isoformat(), "to_date": date(today.year - 1, 12, 31).isoformat()}

    year_match = re.search(r"\b(?:for|in|during)\s+(\d{4})\b", normalized)
    if year_match:
        year = int(year_match.group(1))
        return {"from_date": date(year, 1, 1).isoformat(), "to_date": date(year, 12, 31).isoformat()}

    range_match = re.search(r"(?:from\s+)?(" + "|".join(MONTHS) + r")\s+(\d{4})\s+(?:to|-|through)\s+(" + "|".join(MONTHS) + r")\s+(\d{4})", normalized)
    if range_match:
        start = _month_range(int(range_match.group(2)), MONTHS[range_match.group(1)])
        end = _month_range(int(range_match.group(4)), MONTHS[range_match.group(3)])
        return {"from_date": start["from_date"], "to_date": end["to_date"]}

    return parse_month_year(normalized)


def _month_range(year: int, month: int) -> dict[str, str]:
    return {"from_date": date(year, month, 1).isoformat(), "to_date": date(year, month, monthrange(year, month)[1]).isoformat()}
