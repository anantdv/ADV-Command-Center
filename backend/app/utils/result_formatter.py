from __future__ import annotations

from typing import Any


def format_table_result(doctype: str, rows: list[dict[str, Any]], fields: list[str], filters: dict[str, Any]) -> dict[str, Any]:
    count = len(rows)
    return {
        "type": "table",
        "title": f"{doctype} Results",
        "summary": (
            f"Found {count} {doctype} record{'s' if count != 1 else ''}."
            if count
            else f"No matching {doctype} records found for the selected filters."
        ),
        "columns": [{"key": field, "label": _label(field), "type": "text"} for field in (fields or list(rows[0].keys()) if rows else fields)],
        "rows": rows,
        "filters_applied": filters,
        "source": {"doctype": doctype, "filters": filters},
    }


def _label(field: str) -> str:
    return field.replace("_", " ").title()
