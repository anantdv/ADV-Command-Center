from pathlib import Path
import asyncio

import pytest

from app.services.document_intake_service import DocumentIntakeService


def test_extraction_debug_rejects_unprocessed_intake(tmp_path: Path):
    service = DocumentIntakeService()
    service.root = tmp_path
    intake_dir = tmp_path / "intake_test"
    intake_dir.mkdir()
    (intake_dir / "metadata.json").write_text('{"intake_id":"intake_test","status":"uploaded"}')

    with pytest.raises(Exception):
        asyncio.run(service.extraction_debug("intake_test"))
