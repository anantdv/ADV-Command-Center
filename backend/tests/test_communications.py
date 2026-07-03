import os
from pathlib import Path

import pytest


def ok(response):
    assert response.status_code==200,response.text
    body=response.json();assert body["success"] is True;return body["data"]


def test_communication_inbox_and_thread(client):
    inbox=ok(client.get("/api/communications?folder=inbox"))
    assert inbox["total"]>=1
    assert inbox["items"][0]["sent_or_received"]=="Received"
    thread=ok(client.get(f"/api/communications/{inbox['items'][0]['name']}"))
    assert thread["messages"][0]["content"]
    assert thread["reference_doctype"]=="Lead"


def test_sent_search_and_templates(client):
    sent=ok(client.get("/api/communications?folder=sent&search=delivery"))
    assert sent["items"][0]["sent_or_received"]=="Sent"
    templates=ok(client.get("/api/communications/templates"))
    rendered=ok(client.post(f"/api/communications/templates/{templates[0]['name']}/render",json={"context":{}}))
    assert rendered["response"]


def test_send_reply_link_ai_and_conversion_are_explicit(client):
    sent=ok(client.post("/api/communications/send",json={"to":["customer@example.com"],"subject":"Test","content":"Hello","cc":[],"bcc":[],"attachments":[]}))
    assert sent["message"]
    reply=ok(client.post("/api/communications/COMM-0001/reply",json={"content":"Thanks","cc":[],"bcc":[],"attachments":[]}))
    assert reply["name"]
    linked=ok(client.post("/api/communications/COMM-0001/link",json={"reference_doctype":"Lead","reference_name":"CRM-LEAD-0001"}))
    assert linked["name"]
    draft=ok(client.post("/api/communications/ai/draft",json={"communication_name":"COMM-0001","instruction":"Draft Reply"}))
    assert draft["requires_review"] is True
    converted=ok(client.post("/api/communications/COMM-0001/convert",json={"action":"issue"}))
    assert converted["message"]


def test_companion_communication_api_has_no_permission_bypass():
    companion_root = Path(
        os.environ.get(
            "AI_COMMAND_CENTER_COMPANION_PATH",
            Path(__file__).parents[2] / "apps/ai_command_center",
        )
    )
    api_file = companion_root / "ai_command_center/api/communications.py"
    if not api_file.is_file():
        pytest.skip(
            "Companion app is maintained in a separate repository; set "
            "AI_COMMAND_CENTER_COMPANION_PATH to enable its source audit."
        )
    source=api_file.read_text(encoding="utf-8")
    assert "ignore_permissions" not in source
    assert "frappe.db.sql" not in source
    assert "frappe.get_all" not in source
    assert "frappe.db.get_list" in source
    assert "frappe.sendmail" in source
