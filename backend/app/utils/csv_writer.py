import csv
from io import StringIO
from typing import Any


def write_csv(rows: list[dict[str, Any]]) -> bytes:
    columns = list(dict.fromkeys(key for row in rows for key in row))
    stream = StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=columns, extrasaction="ignore")
    if columns:
        writer.writeheader()
        writer.writerows(rows)
    return ("\ufeff" + stream.getvalue()).encode("utf-8")
