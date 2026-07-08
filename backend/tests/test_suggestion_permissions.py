import pytest

from app.schemas.suggestions import SuggestedPrompt, SuggestionContext
from app.utils.suggestion_permission_filter import SuggestionPermissionFilter


@pytest.mark.asyncio
async def test_permission_filter_removes_unavailable_workflow_action():
    suggestions = [
        SuggestedPrompt(id="s1", label="Approve", type="workflow_action", action_type="apply_workflow_action", payload={"action": "Approve"}),
        SuggestedPrompt(id="s2", label="Reject", type="workflow_action", action_type="apply_workflow_action", payload={"action": "Reject"}),
    ]
    filtered = await SuggestionPermissionFilter().filter(suggestions, SuggestionContext(result_type="workflow_detail", workflow_actions=["Approve"]), [])
    assert [item.label for item in filtered] == ["Approve"]


@pytest.mark.asyncio
async def test_permission_filter_removes_export_without_message():
    suggestions = [SuggestedPrompt(id="s1", label="Export", type="export", action_type="export_result")]
    filtered = await SuggestionPermissionFilter().filter(suggestions, SuggestionContext(result_type="table", row_count=10), [])
    assert filtered == []


@pytest.mark.asyncio
async def test_permission_filter_removes_crud_confirmation_without_token():
    suggestions = [SuggestedPrompt(id="s1", label="Confirm Draft", type="crud_confirmation", action_type="confirm_draft")]
    filtered = await SuggestionPermissionFilter().filter(suggestions, SuggestionContext(result_type="crud_preview"), [])
    assert filtered == []
