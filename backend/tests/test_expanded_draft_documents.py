from app.utils.field_mapper import ALLOWED_CREATE_FIELDS


def test_supported_draft_doctypes_are_allowlisted():
    expected = {
        "Customer", "Supplier", "Item", "Lead", "Opportunity", "Quotation",
        "Sales Order", "Purchase Order", "Sales Invoice", "Purchase Invoice",
        "Delivery Note", "Purchase Receipt", "Material Request", "Issue",
        "Project", "Task",
    }
    assert expected.issubset(ALLOWED_CREATE_FIELDS)


def test_prepare_sales_order_draft_requires_confirmation(client):
    response = client.post("/api/chat/message", json={"message": "create sales order for customer Aster Retail Pvt Ltd for 5 ITEM-001 at 1200 each"})
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["intent"] == "crud_create"
    assert any(part["type"] == "record_preview" for part in data["parts"])
    confirmation = next(part for part in data["parts"] if part["type"] == "confirmation")
    assert confirmation["confirm_label"] == "Create Draft"


def test_missing_items_returns_missing_fields(client):
    response = client.post("/api/chat/message", json={"message": "create purchase invoice for supplier Acme Supplies bill number INV-1001"})
    assert response.status_code == 200
    parts = response.json()["data"]["parts"]
    missing = next(part for part in parts if part["type"] == "missing_fields")
    assert any(field["fieldname"] == "items" for field in missing["fields"])


def test_submit_stays_blocked(client):
    response = client.post("/api/chat/message", json={"message": "submit sales invoice SINV-2026-0418"})
    assert response.status_code == 200
    assert response.json()["data"]["permission"]["allowed"] is False
