from app.utils.detail_intent_parser import parse_detail_intent


def _send(client, message: str):
    response = client.post("/api/chat/message", json={"message": message})
    assert response.status_code == 200, response.text
    return response.json()["data"]


def _part(data, part_type: str):
    return next(item for item in data["parts"] if item["type"] == part_type)


def test_detail_parser_resolves_sales_invoice_prefix():
    intent = parse_detail_intent("show detail for ACC-SINV-2026-00122")
    assert intent.matched is True
    assert intent.doctype == "Sales Invoice"
    assert intent.name == "ACC-SINV-2026-00122"


def test_detail_parser_resolves_explicit_doctype_and_name():
    intent = parse_detail_intent("open purchase order PUR-ORD-2026-00001")
    assert intent.matched is True
    assert intent.doctype == "Purchase Order"
    assert intent.name == "PUR-ORD-2026-00001"


def test_chat_returns_record_detail_part(client):
    data = _send(client, "show details for ACC-SINV-2026-00122")
    assert data["intent"] == "get_record"
    assert data["source"]["source_name"] == "Sales Invoice"
    assert _part(data, "tool_call")["tool_name"] == "get_document_detail"
    detail = _part(data, "record_detail")
    assert detail["doctype"] == "Sales Invoice"
    assert detail["name"] == "ACC-SINV-2026-00122"
    assert "generic" not in data["content"].lower()


def test_document_detail_endpoint_returns_normalized_detail(client):
    response = client.get("/api/erpnext/documents/Sales%20Invoice/ACC-SINV-2026-00122")
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["success"] is True
    assert body["data"]["doctype"] == "Sales Invoice"
    assert body["data"]["name"] == "ACC-SINV-2026-00122"
    assert "summary" in body["data"]
