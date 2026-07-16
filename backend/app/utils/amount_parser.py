from __future__ import annotations

import re


def parse_amount(value: str | None) -> float | None:
    if not value:
        return None
    text = str(value)
    match = re.search(r"[-+]?\d[\d,\s]*(?:\.\d+)?", text)
    if not match:
        return None
    cleaned = match.group(0).replace(",", "").replace(" ", "")
    try:
        return float(cleaned)
    except ValueError:
        return None


def extract_amount_after_labels(lines: list[str], labels: list[str]) -> float | None:
    label_pattern = "|".join(re.escape(label) for label in labels)
    for line in lines:
        match = re.search(rf"\b(?:{label_pattern})\b\s*:?\s*(?:PGK|FJD|USD|AUD|INR|\$)?\s*([0-9][0-9,\s]*(?:\.\d+)?)", line, flags=re.I)
        if match:
            amount = parse_amount(match.group(1))
            if amount is not None:
                return amount
    return None
