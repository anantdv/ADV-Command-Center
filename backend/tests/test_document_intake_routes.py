from io import BytesIO


def test_document_intake_health_returns_json(client):
    response = client.get("/api/document-intake/health")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/json")
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["status"] == "ok"


def test_upload_without_file_returns_json_error(client):
    response = client.post("/api/document-intake/upload")
    assert response.status_code == 422
    assert response.headers["content-type"].startswith("application/json")
    payload = response.json()
    assert payload["success"] is False
    assert payload["error"]["code"] == "validation_error"


def test_invalid_file_type_returns_json_error(client):
    response = client.post(
        "/api/document-intake/upload",
        files={"file": ("bad.exe", BytesIO(b"not allowed"), "application/octet-stream")},
    )
    assert response.status_code == 415
    payload = response.json()
    assert payload["success"] is False
    assert payload["error"]["code"] == "invalid_file_type"


def test_missing_mapping_preview_returns_json_error(client):
    response = client.get("/api/document-intake/intake_missing/mapping-preview")
    assert response.status_code == 404
    payload = response.json()
    assert payload["success"] is False
    assert "not found" in payload["message"].lower()
