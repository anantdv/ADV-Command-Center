def _send(client, message: str):
    response = client.post("/api/chat/message", json={"message": message})
    assert response.status_code == 200, response.text
    return response.json()["data"]


def _part(data, part_type: str):
    return next(item for item in data["parts"] if item["type"] == part_type)


def test_table_result_includes_clickable_row_metadata(client):
    data = _send(client, "show customers")
    table = _part(data, "table")
    assert table["row_action"]["type"] == "open_detail"
    first = table["rows"][0]
    assert first["_meta"] == {"doctype": "Customer", "name": first["name"], "clickable": True}


def test_row_click_detail_prompt_returns_record_detail(client):
    data = _send(client, "show detail for Customer CUST-0001")
    assert data["intent"] == "get_record"
    detail = _part(data, "record_detail")
    assert detail["doctype"] == "Customer"
    assert detail["name"] == "CUST-0001"
