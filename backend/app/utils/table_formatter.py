from typing import Any

from app.schemas.chat import TableColumn, TablePart


def build_table_part(title: str, rows: list[dict[str, Any]], max_rows: int = 20) -> TablePart:
    preview = rows[:max_rows]
    keys: list[str] = []
    for row in preview:
        for key in row:
            if key not in keys:
                keys.append(key)
    columns = [
        TableColumn(key=key, label=key.replace("_", " ").title(), type=_column_type(key, preview))
        for key in keys
    ]
    return TablePart(
        title=title,
        columns=columns,
        rows=preview,
        total_rows=len(rows),
    )


def _column_type(key: str, rows: list[dict[str, Any]]) -> str:
    values = [row.get(key) for row in rows if row.get(key) is not None]
    if values and all(isinstance(value, (int, float)) and not isinstance(value, bool) for value in values):
        return "number"
    if "date" in key or key.endswith("_on"):
        return "date"
    return "text"
