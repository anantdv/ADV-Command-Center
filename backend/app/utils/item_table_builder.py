from __future__ import annotations

from typing import Any


SALES_DOCUMENTS = {"Quotation", "Sales Order", "Sales Invoice", "Delivery Note"}
PURCHASE_DOCUMENTS = {"Purchase Order", "Purchase Invoice", "Purchase Receipt"}
STOCK_DOCUMENTS = {"Stock Entry"}


def normalize_items_for_doctype(doctype: str, items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Normalize user/OCR item rows to ERPNext child-table-compatible keys.

    This does not create or resolve missing Items. Missing item_code rows are
    preserved with a warning marker so the caller can ask the user to choose a
    real Item before confirmation.
    """
    normalized: list[dict[str, Any]] = []
    for item in items or []:
        row = {
            "item_code": item.get("item_code"),
            "item_name": item.get("item_name"),
            "item_query": item.get("item_query"),
            "source_text": item.get("source_text"),
            "row_id": item.get("row_id"),
            "description": item.get("description") or item.get("item_name") or item.get("item_code") or item.get("item_query"),
            "qty": _number(item.get("qty")) or 1,
            "uom": item.get("uom") or item.get("stock_uom"),
            "stock_uom": item.get("stock_uom") or item.get("uom"),
            "conversion_factor": _number(item.get("conversion_factor")) or (1 if item.get("uom") or item.get("stock_uom") else None),
        }
        if doctype in SALES_DOCUMENTS | PURCHASE_DOCUMENTS:
            row["rate"] = _number(item.get("rate")) or 0
            row["amount"] = _number(item.get("amount")) or (row["qty"] * row["rate"])
        if doctype in {"Quotation", "Sales Order", "Delivery Note"} and item.get("delivery_date"):
            row["delivery_date"] = item["delivery_date"]
        if doctype in {"Purchase Order", "Material Request"} and item.get("schedule_date"):
            row["schedule_date"] = item["schedule_date"]
        if doctype in STOCK_DOCUMENTS and item.get("warehouse"):
            row["s_warehouse"] = item.get("s_warehouse") or item.get("warehouse")
            row["t_warehouse"] = item.get("t_warehouse") or item.get("warehouse")
        if doctype == "Material Request":
            row.pop("rate", None)
            row.pop("amount", None)
            if item.get("warehouse"):
                row["warehouse"] = item["warehouse"]
        elif item.get("warehouse"):
            row["warehouse"] = item["warehouse"]
        if item.get("schedule_date") and "schedule_date" not in row:
            row["schedule_date"] = item["schedule_date"]
        if item.get("rate_source"):
            row["rate_source"] = item["rate_source"]
        if not row.get("item_code") and (row.get("item_query") or row.get("item_name")):
            row["_warning"] = "Item is unresolved. Please select an existing ERPNext Item before creating the draft."
        normalized.append({key: value for key, value in row.items() if value not in (None, "")})
    return normalized


def item_warnings(items: list[dict[str, Any]]) -> list[str]:
    return [str(item["_warning"]) for item in items if item.get("_warning")]


def strip_internal_item_markers(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    internal = {"source_text", "row_id", "rate_source", "is_stock_item"}
    return [{key: value for key, value in item.items() if not key.startswith("_") and not key.endswith("_query") and key not in internal} for item in items]


def _number(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    try:
        return float(str(value).replace(",", "").replace("₹", "").strip())
    except ValueError:
        return None
