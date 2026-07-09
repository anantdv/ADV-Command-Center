def assert_success(response):
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["success"] is True
    assert body["data"] is not None
    return body["data"]


def test_auth_me(client):
    data = assert_success(client.get("/api/auth/me"))
    assert data["user"] == "admin@example.com"
    assert "System Manager" in data["roles"]
    assert data["companyCurrency"] == "INR"


def test_dashboard_overview(client):
    data = assert_success(client.get("/api/dashboard/overview"))
    assert len(data["kpis"]) == 8
    assert data["kpis"][0]["title"] == "Total Customers"
    assert data["kpis"][0]["permission"]["allowed"] is True


def test_chat_conversations(client):
    data = assert_success(client.get("/api/chat/conversations"))
    assert data[0]["id"] == "conv-welcome"
    assert data[0]["title"].startswith("Welcome")


def test_chat_overdue_invoice_message(client):
    data = assert_success(client.post("/api/chat/message", json={"conversationId":"conv-overdue","content":"Show overdue invoices"}))
    assert "4 overdue" in data["content"]
    assert any(part["type"] == "chart" for part in data["parts"])


def test_modules(client):
    data = assert_success(client.get("/api/modules"))
    names = {item["name"] for item in data}
    assert {"Accounts", "Selling", "Buying", "Stock", "CRM", "Projects", "Support", "HR", "Assets", "Manufacturing"}.issubset(names)


def test_library_files(client):
    data = assert_success(client.get("/api/library/files"))
    assert any(file["name"].endswith(".xlsx") for file in data)


def test_training_courses(client):
    data = assert_success(client.get("/api/training/courses"))
    assert len(data) >= 5


def test_support_tickets(client):
    data = assert_success(client.get("/api/support/tickets"))
    assert data[0]["priority"] == "High"


def test_erpnext_context(client):
    data = assert_success(client.get("/api/erpnext/current-user-context"))
    assert data["company"] == "ABC Corporation"
    assert data["companyCurrency"] == "INR"


def test_erpnext_list_records(client):
    data = assert_success(client.post("/api/erpnext/list-records", json={"doctype":"Sales Invoice","fields":["name","customer"]}))
    assert data["total"] == 1
    assert data["records"][0]["name"] == "SINV-2026-0418"


def test_erpnext_read_contract_and_direct_create_is_blocked(client):
    created = client.post("/api/erpnext/create-record", json={"doctype": "Quotation", "data": {"party_name": "ABC Customer"}})
    assert created.status_code == 409
    assert "confirmation workflow" in created.json()["message"]
    listed = assert_success(client.post("/api/erpnext/list-records", json={"doctype": "Customer", "limit": 10, "orderBy": "name asc"}))
    assert listed["total"] >= 1


def test_erpnext_direct_update_is_blocked(client):
    updated = client.post("/api/erpnext/update-record", json={"doctype": "Quotation", "name": "QTN-0001", "values": {"valid_till": "2026-08-31"}})
    assert updated.status_code == 409
    assert "confirmation workflow" in updated.json()["message"]
