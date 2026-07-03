import re
from pathlib import Path

from app.config import settings
from app.core.exceptions import AppError
from app.llm.privacy_gateway import assert_safe_knowledge_content
from app.utils.document_reader import extract_text


class DocumentIngestionService:
    def __init__(self, root: str | None = None):
        self.root = Path(root or settings.knowledge_storage_root).resolve()
        self.upload_root = self.root / "uploads"
        self.upload_root.mkdir(parents=True, exist_ok=True)

    def get_source_text(self, record: dict) -> str:
        content_path = record.get("content_path")
        if content_path:
            path = Path(content_path).resolve()
            if not path.is_relative_to(self.root):
                raise AppError("Invalid knowledge content path.", 403)
            text = path.read_text(encoding="utf-8")
        elif record.get("file_id"):
            file_id = str(record["file_id"])
            if not re.fullmatch(r"[A-Za-z0-9_.-]+", file_id):
                raise AppError("Invalid knowledge file identifier.", 422)
            matches = list(self.upload_root.glob(f"{file_id}.*"))
            if len(matches) != 1:
                raise AppError("Registered knowledge file was not found.", 404)
            text = extract_text(str(matches[0]))
        else:
            raise AppError("Knowledge source has no content or registered file.", 422)
        assert_safe_knowledge_content(text)
        return text

    def save_inline_content(self, source_id: str, content: str) -> str:
        assert_safe_knowledge_content(content)
        content_dir = self.root / "sources" / source_id
        content_dir.mkdir(parents=True, exist_ok=True)
        path = content_dir / "content.txt"
        path.write_text(content, encoding="utf-8")
        return str(path)
