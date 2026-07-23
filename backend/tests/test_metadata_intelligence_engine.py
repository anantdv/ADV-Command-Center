import pytest

from app.schemas.common import PermissionMeta
from app.schemas.erpnext import DoctypeSchema, FieldSchema, ListRecordsResponse
from app.schemas.entity_resolution import EntitySearchRequest
from app.services.entity_resolution_service import EntityResolutionService
from app.services.metadata_service import MetadataService
from app.services.schema_cache import SchemaCache


class FakeMetadataERP:
    async def get_doctype_schema(self, doctype: str, cookies=None):
        if doctype == "Purchase Order":
            return DoctypeSchema(
                doctype="Purchase Order",
                module="Buying",
                is_submittable=True,
                fields=[
                    FieldSchema(fieldname="supplier", label="Supplier", fieldtype="Link", options="Supplier", required=True),
                    FieldSchema(fieldname="company", label="Company", fieldtype="Link", options="Company", required=True),
                    FieldSchema(fieldname="items", label="Items", fieldtype="Table", options="Purchase Order Item", required=True),
                ],
                permissions=PermissionMeta(allowed=True, can_read=True, can_create=True),
            )
        return DoctypeSchema(
            doctype="Purchase Order Item",
            module="Buying",
            fields=[
                FieldSchema(fieldname="item_code", label="Item", fieldtype="Link", options="Item", required=True),
                FieldSchema(fieldname="qty", label="Quantity", fieldtype="Float", required=True),
                FieldSchema(fieldname="rate", label="Rate", fieldtype="Currency"),
                FieldSchema(fieldname="warehouse", label="Warehouse", fieldtype="Link", options="Warehouse"),
            ],
            permissions=PermissionMeta(allowed=True, can_read=True),
        )


class FakeEntityERP:
    async def get_doctype_schema(self, doctype: str, cookies=None):
        return DoctypeSchema(
            doctype=doctype,
            module="Custom",
            fields=[
                FieldSchema(fieldname="name", label="Name", fieldtype="Data"),
                FieldSchema(fieldname="vehicle_name", label="Vehicle Name", fieldtype="Data"),
                FieldSchema(fieldname="policy_no", label="Policy No", fieldtype="Data"),
            ],
            permissions=PermissionMeta(allowed=True, can_read=True),
        )

    async def list_records(self, doctype, filters=None, fields=None, limit=20, order_by=None, cookies=None):
        return ListRecordsResponse(
            records=[
                {"name": "VEH-INS-001", "vehicle_name": "Toyota Hilux", "policy_no": "POL-001"},
                {"name": "VEH-INS-002", "vehicle_name": "Ford Ranger", "policy_no": "POL-002"},
            ],
            total=2,
            permissions=PermissionMeta(allowed=True, can_read=True),
        )

    async def search_link(self, doctype, txt, cookies=None, limit=10):
        return []


@pytest.mark.asyncio
async def test_metadata_engine_detects_links_child_tables_and_semantics():
    service = MetadataService(erp=FakeMetadataERP(), cache=SchemaCache())
    intelligence = await service.get_doctype_intelligence("Purchase Order")

    assert intelligence.doctype == "Purchase Order"
    assert intelligence.is_submittable is True
    assert "supplier" in intelligence.mandatory_fields
    assert intelligence.link_fields[0].link_to == "Supplier"
    assert "vendor" in intelligence.link_fields[0].aliases
    assert intelligence.child_tables[0].child_doctype == "Purchase Order Item"
    assert "item_code" in intelligence.child_tables[0].required_fields
    assert intelligence.child_tables[0].field_priority[:2] == ["item_code", "qty"]


@pytest.mark.asyncio
async def test_metadata_driven_entity_resolution_supports_custom_doctype():
    fake_erp = FakeEntityERP()
    service = EntityResolutionService(erp=fake_erp, metadata=MetadataService(erp=fake_erp, cache=SchemaCache()))
    response = await service.search(EntitySearchRequest(doctype="Vehicle Insurance", query="hilux"))

    assert response.doctype == "Vehicle Insurance"
    assert response.matches
    assert response.matches[0].value == "VEH-INS-001"


def test_metadata_api_contract(client):
    response = client.get("/api/metadata/doctypes/Customer/intelligence")
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["doctype"] == "Customer"
    assert "fields" in data
    assert "search" in data
