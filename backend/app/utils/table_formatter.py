from typing import Any

from app.schemas.chat import TableColumn, TablePart


def build_table_part(
    title: str,
    rows: list[dict[str, Any]],
    max_rows: int = 20,
    doctype: str | None = None,
    result_id: str | None = None,
    config: dict[str, Any] | None = None,
) -> TablePart:
    preview = [_with_row_meta(row, doctype) for row in rows[:max_rows]]
    keys: list[str] = []
    for row in preview:
        for key in row:
            if key.startswith("_"):
                continue
            if key not in keys:
                keys.append(key)
    columns = [
        TableColumn(key=key, label=key.replace("_", " ").title(), type=_column_type(key, preview))
        for key in keys
    ]
    return TablePart(
        result_id=result_id,
        title=title,
        columns=columns,
        rows=preview,
        total_rows=len(rows),
        config=config or {},
        row_action={"type": "open_detail", "endpoint": "/api/erpnext/documents/{doctype}/{name}"} if _has_clickable_rows(preview) else None,
    )


def _column_type(key: str, rows: list[dict[str, Any]]) -> str:
    values = [row.get(key) for row in rows if row.get(key) is not None]
    if values and all(isinstance(value, (int, float)) and not isinstance(value, bool) for value in values):
        return "number"
    if "date" in key or key.endswith("_on"):
        return "date"
    return "text"


def _with_row_meta(row: dict[str, Any], doctype: str | None) -> dict[str, Any]:
    output = dict(row)
    row_doctype = doctype or _string_value(row.get("doctype"))
    name = _string_value(row.get("name"))
    if row_doctype and name and not isinstance(output.get("_meta"), dict):
        output["_meta"] = {"doctype": row_doctype, "name": name, "clickable": True}
    return output


def _has_clickable_rows(rows: list[dict[str, Any]]) -> bool:
    return any(isinstance(row.get("_meta"), dict) and row["_meta"].get("clickable") for row in rows)


def _string_value(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None
