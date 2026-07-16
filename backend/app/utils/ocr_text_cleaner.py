from __future__ import annotations

import re


def fix_common_ocr_errors(text: str) -> str:
    replacements = {
        "lnvoice": "Invoice",
        "lnv": "Inv",
        "InvoiceNo": "Invoice No",
        "BillNo": "Bill No",
        "Date:": "Date: ",
    }
    fixed = text or ""
    for source, target in replacements.items():
        fixed = fixed.replace(source, target)
    fixed = re.sub(r"\bInv\s*No\.?\b", "Invoice No", fixed, flags=re.I)
    fixed = re.sub(r"\bBill\s*No\.?\b", "Bill No", fixed, flags=re.I)
    fixed = re.sub(r"([A-Za-z])\s*:\s*([^\s])", r"\1: \2", fixed)
    fixed = re.sub(r"[ \t]+", " ", fixed)
    return fixed


def normalize_ocr_lines(text: str) -> list[str]:
    cleaned = clean_ocr_text(text)
    lines = [re.sub(r"\s+", " ", line).strip() for line in cleaned.splitlines()]
    return remove_empty_noise_lines(lines)


def remove_empty_noise_lines(lines: list[str]) -> list[str]:
    output: list[str] = []
    for line in lines:
        stripped = line.strip(" -_|")
        if not stripped:
            continue
        if len(stripped) == 1 and not stripped.isalnum():
            continue
        output.append(stripped)
    return output


def clean_ocr_text(text: str) -> str:
    fixed = fix_common_ocr_errors(text or "")
    fixed = fixed.replace("\r\n", "\n").replace("\r", "\n")
    fixed = re.sub(r"\n{3,}", "\n\n", fixed)
    return fixed.strip()
