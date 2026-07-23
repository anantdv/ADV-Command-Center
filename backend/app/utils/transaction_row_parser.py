from __future__ import annotations

import re
from typing import Any


TYPO_NORMALIZATIONS = {
    "friyer": "fryer",
    "overn": "oven",
}

PRODUCT_SYNONYMS = {
    "ac": "air conditioner",
}

QUOTED_ITEM = re.compile(r"[\"'“‘](?P<name>.+?)[\"'”’]", re.I)
NUMBER = r"(?P<number>\d+(?:,\d{3})*(?:\.\d+)?)"


class TransactionRowParser:
    """Deterministic parser for natural-language transaction child rows.

    The important invariant: once a quantity/rate/warehouse/UOM token is parsed
    into a structured value, that token is removed from `item_query`.
    """

    QUANTITY_MARKERS = r"qty|quantity|q|x|units?|pcs|pieces|cartons?|boxes|bags?"
    RATE_MARKERS = r"unit\s+price|selling\s+price|buying\s+price|price|rate|cost|per\s+unit|@|at"
    WAREHOUSE_MARKER = r"warehouse|from\s+warehouse|store|location"
    UOM_MARKER = r"uom|unit"

    def parse_many(self, text: str) -> list[dict[str, Any]]:
        body = self._body(text)
        segments = self._segments(body)
        rows = [row for segment in segments if (row := self.parse_one(segment))]
        return rows

    def parse_one(self, text: str) -> dict[str, Any] | None:
        source = " ".join(str(text or "").strip(" ,.;:-").split())
        if not source:
            return None
        if re.search(r"\b(?:create|add|draft|prepare|make|raise|enter)\b", source, re.I) and re.search(r"\b(?:invoice|order|quotation|receipt|po|pi|so|si)\b", source, re.I) and not re.search(r"\b(item|items|qty|quantity|price|rate|@| at |\d+\s+[A-Za-z])\b", source, re.I):
            return None
        if re.search(r"\b(?:create|add|draft|prepare|make|raise|enter|sales|purchase|po|pi|so|si)?\s*(?:invoice|order|quotation|receipt|po|pi|so|si)\b.+\bfor\b", source, re.I) and not re.search(r"\b(qty|quantity|price|rate|@| at |\d+\s+[A-Za-z])", source, re.I):
            return None
        working = self._normalize_text(source)
        row: dict[str, Any] = {"source_text": source}

        quoted = QUOTED_ITEM.search(working)
        if quoted:
            row["item_query"] = self._clean_query(quoted.group("name"))
            working = (working[: quoted.start()] + " " + working[quoted.end() :]).strip()

        qty, working = self._extract_qty(working)
        rate, working = self._extract_rate(working)
        warehouse, working = self._extract_named_value(working, self.WAREHOUSE_MARKER)
        uom, working = self._extract_named_value(working, self.UOM_MARKER)
        discount, working = self._extract_discount(working)

        if qty is not None:
            row["qty"] = qty
        else:
            inferred, working = self._extract_leading_qty(working)
            if inferred is not None:
                row["qty"] = inferred
                row["qty_source"] = "leading_number"
        if rate is not None:
            row["rate"] = rate
            row["rate_source"] = "user"
        if warehouse:
            row["warehouse_query"] = warehouse
        if uom:
            row["uom_query"] = uom
        if discount is not None:
            row["discount_percentage"] = discount

        if not row.get("item_query"):
            row["item_query"] = self._clean_query(working)
        if not row.get("item_query"):
            return None
        row.setdefault("qty", 1)
        row.setdefault("rate", 0)
        row["amount"] = round(float(row["qty"]) * float(row["rate"]), 2)
        row["raw_query"] = row["item_query"]
        row["normalized_query"] = self._clean_query(row["item_query"]).lower()
        row.setdefault("description", row["item_query"])
        return row

    def _body(self, text: str) -> str:
        body = " ".join(str(text or "").strip().split())
        body = re.split(r"\b(?:items\b|item\s+|containing\b|with\b)", body, maxsplit=1, flags=re.I)[-1]
        body = re.split(r"\bfor\s+(?=\d+(?:\.\d+)?\s+[A-Za-z0-9-])", body, maxsplit=1, flags=re.I)[-1]
        body = re.sub(r"^(?:for\s+)?(?:item\s+)?", "", body, flags=re.I).strip()
        return body

    def _segments(self, body: str) -> list[str]:
        body = body.replace(";", "\n")
        body = re.sub(r"\s+\band\b\s+(?=(?:item\s+)?[A-Za-z0-9'\"“‘]|\d+\s+[A-Za-z])", ", ", body, flags=re.I)
        lines = [line.strip(" -•\t") for line in body.splitlines() if line.strip(" -•\t")]
        if len(lines) <= 1:
            lines = [part.strip(" ,.;") for part in re.split(r"\s*,\s*", body) if part.strip(" ,.;")]
        return lines

    def _extract_qty(self, text: str) -> tuple[float | None, str]:
        patterns = [
            rf"\b(?:{self.QUANTITY_MARKERS})\s*[:=]?\s*{NUMBER}\b",
            rf"\b(?P<number>\d+(?:,\d{{3}})*(?:\.\d+)?)\s*(?:{self.QUANTITY_MARKERS})\b",
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.I)
            if match:
                return _num(match.group("number")), _remove_span(text, match.span())
        return None, text

    def _extract_leading_qty(self, text: str) -> tuple[float | None, str]:
        match = re.match(rf"^\s*{NUMBER}\s+(?=[A-Za-z])", text, re.I)
        if not match:
            return None, text
        rest = text[match.end() :].strip()
        if re.match(r"^(?:inch|inches|mm|cm|kg|g|l|ltr|litre|liter)\b", rest, re.I):
            return None, text
        return _num(match.group("number")), rest

    def _extract_rate(self, text: str) -> tuple[float | None, str]:
        patterns = [
            rf"@\s*{NUMBER}\b(?:\s+each\b)?",
            rf"\b(?:each\s+at|{self.RATE_MARKERS})\s*[:=]?\s*{NUMBER}\b(?:\s+each\b)?",
            rf"\b{NUMBER}\s+(?:each|per\s+unit)\b",
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.I)
            if match:
                return _num(match.group("number")), _remove_span(text, match.span())
        return None, text

    def _extract_named_value(self, text: str, marker: str) -> tuple[str | None, str]:
        match = re.search(rf"\b(?:{marker})\s*[:=]?\s+(.+?)(?=\s+\b(?:qty|quantity|price|rate|cost|@|at|discount|tax|uom|warehouse)\b|$)", text, re.I)
        if not match:
            return None, text
        value = self._clean_query(match.group(1))
        return value or None, _remove_span(text, match.span())

    @staticmethod
    def _extract_discount(text: str) -> tuple[float | None, str]:
        match = re.search(rf"\bdiscount\s*[:=]?\s*{NUMBER}\s*%?", text, re.I)
        if not match:
            return None, text
        return _num(match.group("number")), _remove_span(text, match.span())

    @staticmethod
    def _normalize_text(value: str) -> str:
        value = re.sub(r"\bqty(?=\d)", "qty ", value, flags=re.I)
        value = re.sub(r"\bprice(?=\d)", "price ", value, flags=re.I)
        value = re.sub(r"(?<=\d)(inch|inches|ltr|l|kg|mm|cm)\b", r" \1", value, flags=re.I)
        for wrong, right in TYPO_NORMALIZATIONS.items():
            value = re.sub(rf"\b{wrong}\b", right, value, flags=re.I)
        value = re.sub(r"\bmedia(?=\s+split\s+ac\b)", "Midea", value, flags=re.I)
        return " ".join(value.split())

    @staticmethod
    def _clean_query(value: str) -> str:
        value = re.sub(r"^(?:items?|item)\s+", "", value, flags=re.I)
        value = re.sub(r"^item\s+\d+\s+(?=[A-Za-z])", "", value, flags=re.I)
        value = re.sub(r"\b(?:qty|quantity|price|rate|cost|each|per\s+unit|warehouse|uom)\b\s*[:=]?\s*$", "", value, flags=re.I)
        value = re.sub(r"\s+", " ", value).strip(" ,.;:-")
        return value


def _remove_span(text: str, span: tuple[int, int]) -> str:
    return " ".join((text[: span[0]] + " " + text[span[1] :]).split())


def _num(value: str) -> float:
    number = float(str(value).replace(",", ""))
    return int(number) if number.is_integer() else number


transaction_row_parser = TransactionRowParser()
