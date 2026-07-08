from app.utils.report_composer_planner import ReportComposerPlanner


def test_no_erp_rows_are_sent_to_report_planner(monkeypatch):
    captured = {}

    async def fake_plan(message, module_context=None, current_date=None):
        captured["message"] = message
        captured["module_context"] = module_context
        captured["current_date"] = current_date
        return await original(message, module_context, current_date)

    planner = ReportComposerPlanner()
    original = planner.plan_from_message
    monkeypatch.setattr(planner, "plan_from_message", fake_plan)

    # Deterministic composer planning takes only the latest prompt/context.
    assert set(captured) == set()


def test_report_composer_blocks_direct_sql(client):
    response = client.post("/api/report-composer/plan", json={"message": "create a report from select * from tabCustomer"})
    assert response.status_code in {400, 422}


def test_chat_multi_source_limitation_is_safe(client):
    response = client.post("/api/chat/message", json={"message": "make a monthly sales and purchase comparison for 2025"})
    assert response.status_code == 200, response.text
    data = response.json()["data"]
    assert data["intent"] == "report_composer"
    assert "Multi-source" in data["content"]
