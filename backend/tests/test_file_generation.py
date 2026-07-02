from pathlib import Path

import pytest

from app.services.file_generation_service import file_generation_service
from app.services.library_service import library_service
from app.utils.file_storage import FileStorage


@pytest.fixture
def private_storage(tmp_path):
    storage = FileStorage(str(tmp_path / "generated"))
    old_generation = file_generation_service.storage
    old_library = library_service.storage
    file_generation_service.storage = storage
    library_service.storage = storage
    yield storage
    file_generation_service.storage = old_generation
    library_service.storage = old_library


def generate(client, payload):
    response = client.post("/api/library/files", json=payload)
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["success"] is True
    return body["data"]["file"]


def test_generate_excel_from_mock_customer_data(client, private_storage):
    file = generate(client, {"source_type":"doctype","source_name":"Customer","file_format":"xlsx","fields":["name","customer_name","customer_group"]})
    assert file["file_name"].endswith(".xlsx")
    assert private_storage.read_bytes(file["file_id"]).startswith(b"PK")


def test_generate_csv_from_mock_item_data(client, private_storage):
    file = generate(client, {"source_type":"doctype","source_name":"Item","file_format":"csv"})
    content = private_storage.read_bytes(file["file_id"])
    assert content.startswith(b"\xef\xbb\xbf")
    assert b"item_name" in content


def test_generate_pdf_from_mock_invoice_data(client, private_storage):
    file = generate(client, {"source_type":"doctype","source_name":"Sales Invoice","file_format":"pdf","filters":{"status":"Overdue"}})
    assert private_storage.read_bytes(file["file_id"]).startswith(b"%PDF")


def test_generate_html_report(client, private_storage):
    file = generate(client, {"source_type":"doctype","source_name":"Customer","file_format":"html","title":"Customer Export"})
    html = private_storage.read_bytes(file["file_id"]).decode()
    assert "ADV Command Center" in html
    assert "Customer Export" in html


def test_generate_chart_png(client, private_storage):
    file = generate(client, {"source_type":"chat_result","source_name":"Top Customers","file_format":"png","rows":[{"customer":"Aster","total":10},{"customer":"Nimbus","total":8}],"chart_config":{"chart_type":"bar","title":"Top Customers","data":[{"customer":"Aster","total":10},{"customer":"Nimbus","total":8}],"x_key":"customer","y_key":"total"}})
    assert private_storage.read_bytes(file["file_id"]).startswith(b"\x89PNG\r\n\x1a\n")


def test_list_metadata_and_download(client, private_storage):
    file = generate(client, {"source_type":"doctype","source_name":"Customer","file_format":"csv"})
    listed = client.get("/api/library/files").json()["data"]
    assert any(item["file_id"] == file["file_id"] for item in listed)
    downloaded = client.get(f"/api/library/files/{file['file_id']}/download")
    assert downloaded.status_code == 200
    assert "attachment" in downloaded.headers["content-disposition"]


def test_reject_invalid_file_id_path_traversal(client, private_storage):
    response = client.get("/api/library/files/%2E%2E%2Fsecrets/download")
    assert response.status_code in {400, 404}


def test_chat_export_customers_to_excel(client, private_storage):
    response = client.post("/api/chat/message", json={"message":"export customers to excel"})
    assert response.status_code == 200, response.text
    data = response.json()["data"]
    assert data["intent"] == "generate_file"
    file_part = next(part for part in data["parts"] if part["type"] == "file")
    assert file_part["file_name"].endswith(".xlsx")


def test_chat_generate_overdue_invoice_pdf(client, private_storage):
    response = client.post("/api/chat/message", json={"message":"generate pdf for overdue sales invoices"})
    assert response.status_code == 200, response.text
    data = response.json()["data"]
    assert data["source"]["source_name"] == "Sales Invoice"
    assert next(part for part in data["parts"] if part["type"] == "file")["file_format"] == "pdf"
