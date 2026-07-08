from app.schemas.report_composer import ReportComposerPlan, ReportComposerRunRequest, ReportMetric, ReportSource
from app.services.report_composer_service import ReportComposerService
import pytest


def test_report_composer_api_plan_and_run(client):
    plan_response = client.post("/api/report-composer/plan", json={
        "message": "create a report for unpaid invoices grouped by customer with total outstanding"
    })
    assert plan_response.status_code == 200, plan_response.text
    plan = plan_response.json()["data"]
    assert plan["source"]["sourceName"] == "Sales Invoice"
    assert plan["groupBy"] == ["customer"]

    run_response = client.post("/api/report-composer/run", json={"plan": plan})
    assert run_response.status_code == 200, run_response.text
    data = run_response.json()["data"]
    assert data["rows"]
    assert data["chart"]
    assert data["permission"]["allowed"] is True


def test_report_composer_chat_returns_table_and_chart(client):
    response = client.post("/api/chat/message", json={
        "message": "create a report showing sales invoices by customer for May 2025 with invoice count and total amount"
    })
    assert response.status_code == 200, response.text
    data = response.json()["data"]
    assert data["intent"] == "report_composer"
    assert any(part["type"] == "table" for part in data["parts"])
    assert any(part["type"] == "chart" for part in data["parts"])


@pytest.mark.asyncio
async def test_report_composer_service_summary_report():
    service = ReportComposerService()
    result = await service.run_report(ReportComposerRunRequest(plan=ReportComposerPlan(
        source=ReportSource(source_name="Sales Invoice"),
        output_mode="summary",
        group_by=["customer"],
        metrics=[ReportMetric(fieldname="grand_total", function="sum", label="Total Amount")],
    )))
    assert result.rows
    assert result.rows[0]["grand_total_sum"] > 0
