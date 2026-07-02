import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.core.exceptions import AppError

FILE_ID_PATTERN = re.compile(r"^file_[a-zA-Z0-9]{8,64}$")


class FileStorage:
    """Private local storage addressed only by opaque validated file IDs."""

    def __init__(self, root: str):
        self.root = Path(root).expanduser().resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def validate_file_id(file_id: str) -> str:
        if not FILE_ID_PATTERN.fullmatch(file_id):
            raise AppError("Invalid file ID.", 400, {"file_id": "invalid"})
        return file_id

    def _directory(self, file_id: str, create: bool = False) -> Path:
        self.validate_file_id(file_id)
        matches = list(self.root.glob(f"*/*/{file_id}"))
        if matches:
            return matches[0]
        now = datetime.now(timezone.utc)
        target = self.root / str(now.year) / f"{now.month:02d}" / file_id
        if create:
            target.mkdir(parents=True, exist_ok=True)
        return target

    def save_bytes(self, file_id: str, filename: str, content: bytes) -> str:
        directory = self._directory(file_id, create=True)
        safe_name = Path(filename).name
        if not safe_name or safe_name in {".", "..", "metadata.json"}:
            raise AppError("Invalid file name.", 400)
        path = (directory / safe_name).resolve()
        if path.parent != directory.resolve():
            raise AppError("Invalid file name.", 400)
        path.write_bytes(content)
        return str(path)

    def save_text(self, file_id: str, filename: str, content: str) -> str:
        return self.save_bytes(file_id, filename, content.encode("utf-8"))

    def save_metadata(self, file_id: str, metadata: dict[str, Any]) -> None:
        directory = self._directory(file_id, create=True)
        (directory / "metadata.json").write_text(
            json.dumps(metadata, ensure_ascii=False, indent=2, default=str),
            encoding="utf-8",
        )

    def read_metadata(self, file_id: str) -> dict[str, Any]:
        path = self._directory(file_id) / "metadata.json"
        if not path.is_file():
            raise AppError("Generated file was not found.", 404, {"file_id": file_id})
        return json.loads(path.read_text(encoding="utf-8"))

    def list_metadata(self) -> list[dict[str, Any]]:
        records: list[dict[str, Any]] = []
        for path in self.root.glob("*/*/file_*/metadata.json"):
            try:
                records.append(json.loads(path.read_text(encoding="utf-8")))
            except (OSError, ValueError, TypeError):
                continue
        return sorted(records, key=lambda item: str(item.get("created_at", "")), reverse=True)

    def get_file_path(self, file_id: str) -> Path:
        metadata = self.read_metadata(file_id)
        directory = self._directory(file_id).resolve()
        path = (directory / Path(str(metadata.get("file_name", ""))).name).resolve()
        if path.parent != directory or not path.is_file():
            raise AppError("Generated file was not found.", 404, {"file_id": file_id})
        return path

    def exists(self, file_id: str) -> bool:
        try:
            return self.get_file_path(file_id).is_file()
        except AppError:
            return False

    def read_bytes(self, file_id: str) -> bytes:
        return self.get_file_path(file_id).read_bytes()

    def delete(self, file_id: str) -> None:
        directory = self._directory(file_id)
        if not directory.is_dir():
            raise AppError("Generated file was not found.", 404, {"file_id": file_id})
        for child in directory.iterdir():
            if child.is_file():
                child.unlink()
        directory.rmdir()
