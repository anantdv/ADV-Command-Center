from app.schemas.task_plan import PlanStatus


def _send(client, message: str, conversation_id: str | None = None, structured_action: dict | None = None):
    payload = {"message": message}
    if conversation_id:
        payload["conversation_id"] = conversation_id
    if structured_action:
        payload["structured_action"] = structured_action
        payload["source"] = "generated_action"
    response = client.post("/api/chat/message", json=payload)
    assert response.status_code == 200, response.text
    return response.json()["data"]


def _plan_part(data: dict) -> dict:
    return next(part for part in data["parts"] if part["type"] == "execution_plan")


def test_create_po_originates_from_execution_plan(client):
    data = _send(client, "create po for bnbm")
    plan = _plan_part(data)

    assert data["intent"] in {"child_rows_resolution_required", "crud_create"}
    assert data["current_state"] in {"DRAFT_ENTITY_RESOLUTION", "DRAFT_INFORMATION_REQUIRED", "DRAFT_COLLECTING"}
    assert data["response_type"] in {"entity_selection", "draft_information_required", "crud_create"}
    assert plan["title"].lower().startswith("prepare purchase order")
    assert [step["action"] for step in plan["steps"]][:4] == [
        "ResolveEntity",
        "ResolveItems",
        "ResolveWarehouse",
        "DiscoverRelationships",
    ]
    assert any(step["action"] == "Validate" for step in plan["steps"])
    assert "blocked" not in data["content"].lower()


def test_plan_inspection_api_lists_conversation_plans(client):
    data = _send(client, "show customers")
    plan = _plan_part(data)

    response = client.get(f"/api/task-plans/{plan['plan_id']}")
    assert response.status_code == 200
    loaded = response.json()["data"]
    assert loaded["id"] == plan["plan_id"]
    assert loaded["conversation_id"] == data["conversation_id"]

    listed = client.get(f"/api/task-plans/conversation/{data['conversation_id']}")
    assert listed.status_code == 200
    assert any(item["id"] == plan["plan_id"] for item in listed.json()["data"])


def test_report_followup_runs_through_plan(client):
    first = _send(client, "show customers")
    chart = _send(client, "show this result as a chart", first["conversation_id"])
    plan = _plan_part(chart)

    assert chart["response_type"] == "report_result"
    assert plan["status"] in {PlanStatus.COMPLETED.value, PlanStatus.WAITING_USER.value}
    assert any(step["action"] == "GenerateChart" for step in plan["steps"])
    assert any(part["type"] == "chart" for part in chart["parts"])


def test_plan_cancel_and_retry_api(client):
    data = _send(client, "show customers")
    plan_id = _plan_part(data)["plan_id"]

    cancelled = client.post(f"/api/task-plans/{plan_id}/cancel")
    assert cancelled.status_code == 200
    assert cancelled.json()["data"]["status"] == "cancelled"

    retry = client.post(f"/api/task-plans/{plan_id}/retry")
    assert retry.status_code == 200
    assert retry.json()["data"]["id"] == plan_id


def test_confirmed_draft_write_has_execution_plan(client):
    data = _send(client, "create customer Blue Ocean Trading with customer group Commercial and territory India")
    confirmation = next(part for part in data["parts"] if part["type"] == "confirmation")

    response = client.post("/api/chat/actions/confirm", json={"confirmation_id": confirmation["confirmation_id"]})
    assert response.status_code == 200

    plans = client.get(f"/api/task-plans/conversation/{data['conversation_id']}")
    assert plans.status_code == 200
    assert any(
        plan["metadata"].get("confirmation_id") == confirmation["confirmation_id"]
        and any(step["action"] == "CreateDraft" for step in plan["steps"])
        for plan in plans.json()["data"]
    )
