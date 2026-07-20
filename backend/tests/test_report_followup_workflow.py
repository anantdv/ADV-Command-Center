import pytest

from app.schemas.chat import ChatMessageRequest, ConversationCreate
from app.services.chat_service import ChatService
from app.utils.datetime import utc_now


MONTHLY_ROWS_UNSORTED = [
    {"period": "Jun 2026", "grand_total_sum": 500},
    {"period": "Jan 2026", "grand_total_sum": 204705},
    {"period": "Mar 2026", "grand_total_sum": 1000},
    {"period": "Feb 2026", "grand_total_sum": 700},
    {"period": "May 2026", "grand_total_sum": 300},
    {"period": "Apr 2026", "grand_total_sum": 1200},
]


async def _service_with_report_context() -> tuple[ChatService, str]:
    service = ChatService()
    conversation = await service.create_conversation(ConversationCreate(title="Sales invoices"))
    await service.repository.save_result_context(
        conversation.id,
        {
            "report_id": "report_sales_2026",
            "result_id": "result_monthly_sales_2026",
            "conversation_id": conversation.id,
            "message_id": "msg_report",
            "intent": "sales_invoice_analysis",
            "doctype": "Sales Invoice",
            "source_type": "doctype",
            "source_name": "Sales Invoice",
            "title": "Monthly Sales Trend",
            "columns": ["period", "grand_total_sum"],
            "filters": {"docstatus": 1, "posting_date": ["between", ["2026-01-01", "2026-06-30"]]},
            "rows": MONTHLY_ROWS_UNSORTED,
            "chart": None,
            "row_count": len(MONTHLY_ROWS_UNSORTED),
            "created_at": utc_now().isoformat(),
        },
    )
    return service, conversation.id


@pytest.mark.asyncio
async def test_followup_chart_uses_active_report_context_and_sorts_months():
    service, conversation_id = await _service_with_report_context()

    response = await service.send_chat_message(
        ChatMessageRequest(
            conversation_id=conversation_id,
            message="Summarize this result as a chart. Use the same filters.",
        )
    )

    assert response.intent == "chart_result"
    assert "I can help with ERPNext queries" not in response.content
    chart = next(part for part in response.parts if part.type == "chart")
    assert chart.config["parent_result_id"] == "result_monthly_sales_2026"
    assert [row["period"] for row in chart.data] == [
        "Jan 2026",
        "Feb 2026",
        "Mar 2026",
        "Apr 2026",
        "May 2026",
        "Jun 2026",
    ]


@pytest.mark.asyncio
async def test_structured_generated_action_visualizes_same_result():
    service, conversation_id = await _service_with_report_context()

    response = await service.send_chat_message(
        ChatMessageRequest(
            conversation_id=conversation_id,
            message="Summarize as Chart",
            source="generated_action",
            structured_action={
                "action": "transform_report",
                "operation": "visualize",
                "visualization": "auto",
                "result_id": "result_monthly_sales_2026",
                "preserve_filters": True,
                "preserve_grouping": True,
                "source": "generated_action",
            },
        )
    )

    assert response.intent == "chart_result"
    assert any(part.type == "chart" for part in response.parts)


@pytest.mark.asyncio
async def test_group_by_customer_preserves_filters_and_requeries():
    service, conversation_id = await _service_with_report_context()

    response = await service.send_chat_message(
        ChatMessageRequest(
            conversation_id=conversation_id,
            message="Group this report by customer",
            source="generated_action",
            structured_action={
                "action": "transform_report",
                "operation": "regroup",
                "group_by": "customer",
                "result_id": "result_monthly_sales_2026",
                "preserve_filters": True,
            },
        )
    )

    assert response.intent == "report_result"
    assert response.source
    assert response.source.filters["docstatus"] == 1
    assert any(part.type == "table" for part in response.parts)


@pytest.mark.asyncio
async def test_unclear_command_without_context_returns_clarification_not_welcome():
    response = await ChatService().send_chat_message(ChatMessageRequest(message="make it nicer somehow"))

    assert response.intent == "clarification_required"
    assert "I can help with ERPNext queries" not in response.content
    assert "could not determine" in response.content.lower()
