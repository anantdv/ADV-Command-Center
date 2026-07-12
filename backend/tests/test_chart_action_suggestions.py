from app.schemas.suggestions import SuggestionContext
from app.utils.suggestion_rules import get_suggestions_for_context


def test_chart_result_actions_are_typed_ui_actions():
    suggestions = get_suggestions_for_context(
        SuggestionContext(
            conversation_id="conv_1",
            message_id="msg_1",
            result_type="analytics",
            source_type="doctype",
            source_name="Sales Invoice",
            doctype="Sales Invoice",
            row_count=12,
            has_chart=True,
            chart_type="line",
            columns=["period", "grand_total_sum"],
            extra={"result_id": "res_123"},
        )
    )
    by_label = {item.label: item for item in suggestions}
    assert by_label["Change Chart Type"].type == "ui_action"
    assert by_label["Change Columns"].type == "ui_action"
    assert by_label["Refine Filters"].type == "ui_action"
    assert by_label["Save Report View"].type == "ui_action"
    assert by_label["Change Chart Type"].payload["result_id"] == "res_123"
    assert by_label["Export to Excel"].payload["format"] == "xlsx"


def test_chart_result_actions_disable_without_context():
    suggestions = get_suggestions_for_context(
        SuggestionContext(result_type="analytics", row_count=5, has_chart=True, chart_type="bar")
    )
    change = next(item for item in suggestions if item.label == "Change Chart Type")
    assert change.disabled is True
    assert "active result" in (change.disabled_reason or "")
