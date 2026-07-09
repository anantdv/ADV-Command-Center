import pytest

from app.services.dashboard_service import dashboard_service


@pytest.fixture(autouse=True)
def clear_widgets():
    dashboard_service.clear_for_tests()
    yield
    dashboard_service.clear_for_tests()


def ok(response):
    assert response.status_code == 200, response.text
    body=response.json();assert body["success"] is True
    return body["data"]


TABLE={"title":"Customer Directory","widget_type":"table","source":{"source_type":"doctype","doctype":"Customer","fields":["name","customer_name"]}}
KPI={"title":"Total Customers","widget_type":"kpi","source":{"source_type":"doctype","doctype":"Customer","aggregate_function":"count"}}


def test_dashboard_overview_has_real_widget_contract(client):
    data=ok(client.get('/api/dashboard/overview'))
    assert len(data['kpis'])==8
    assert data['widgets']
    assert data['kpis'][0]['permission']['allowed'] is True


def test_create_and_list_table_widget(client):
    created=ok(client.post('/api/dashboard/widgets',json=TABLE))
    assert created['widget_type']=='table'
    assert created['data']['rows']
    listed=ok(client.get('/api/dashboard/widgets'))
    assert any(widget['widget_id']==created['widget_id'] for widget in listed)


def test_create_kpi_widget(client):
    created=ok(client.post('/api/dashboard/widgets',json=KPI))
    assert created['data']['value']==2
    assert created['permission']['allowed'] is True


def test_refresh_update_reorder_and_delete_widget(client):
    created=ok(client.post('/api/dashboard/widgets',json=TABLE));wid=created['widget_id']
    refreshed=ok(client.post(f'/api/dashboard/widgets/{wid}/refresh'))
    assert refreshed['last_refreshed_at']
    updated=ok(client.put(f'/api/dashboard/widgets/{wid}',json={'title':'Customers I Can View','refresh_interval_seconds':600}))
    assert updated['title']=='Customers I Can View'
    assert ok(client.post('/api/dashboard/widgets/reorder',json={'layouts':[{'widget_id':wid,'layout':{'x':2,'y':1,'w':6,'h':4}}]})) is True
    assert ok(client.delete(f'/api/dashboard/widgets/{wid}')) is True
    assert ok(client.get('/api/dashboard/widgets'))==[]


def test_pin_chat_result_to_dashboard(client):
    payload={"conversation_id":"conv_123","message_id":"msg_456","title":"Pinned Overdue Sales Invoices","widget_type":"table","source":{"source_type":"doctype","doctype":"Sales Invoice","filters":{"status":"Overdue"},"fields":["name","customer","grand_total","status"]}}
    pinned=ok(client.post('/api/chat/actions/pin-to-dashboard',json=payload))
    assert pinned['widget_id'].startswith('widget_')
    overview=ok(client.get('/api/dashboard/overview'))
    assert any(widget['widget_id']==pinned['widget_id'] for widget in overview['widgets'])


def test_pin_chat_result_to_module_is_not_shown_on_overview(client):
    payload={"conversation_id":"conv_123","message_id":"msg_456","title":"Pinned Selling Customers","widget_type":"table","target_type":"module","module_name":"Selling","source":{"source_type":"doctype","doctype":"Customer","fields":["name","customer_name"]}}
    pinned=ok(client.post('/api/chat/actions/pin-to-dashboard',json=payload))
    overview=ok(client.get('/api/dashboard/overview'))
    selling=ok(client.get('/api/modules/Selling/dashboard'))

    assert not any(widget['widget_id']==pinned['widget_id'] for widget in overview['widgets'])
    assert any(widget['widget_id']==pinned['widget_id'] for widget in selling['pinnedWidgets'])


def test_invalid_and_raw_sql_sources_are_rejected(client):
    invalid=client.post('/api/dashboard/widgets',json={"title":"Bad","widget_type":"table","source":{"source_type":"raw_sql","source_name":"select * from tabCustomer"}})
    assert invalid.status_code==422
    injected=client.post('/api/dashboard/widgets',json={"title":"Bad","widget_type":"table","source":{"source_type":"doctype","doctype":"Customer; DROP TABLE tabUser"}})
    assert injected.status_code==422


def test_sensitive_fields_are_rejected(client):
    response=client.post('/api/dashboard/widgets',json={"title":"Secrets","widget_type":"table","source":{"source_type":"doctype","doctype":"User","fields":["name","api_secret"]}})
    assert response.status_code==422


def test_raw_rows_cannot_be_embedded_in_widget_metadata(client):
    response=client.post('/api/dashboard/widgets',json={**TABLE,"chart_config":{"data":[{"name":"CUST-0001"}]}})
    assert response.status_code==422
