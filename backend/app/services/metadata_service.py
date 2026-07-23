from __future__ import annotations

import hashlib
import re
from typing import Any

from app.config import settings
from app.frappe.client import FrappeClient
from app.schemas.common import PermissionMeta
from app.schemas.erpnext import DoctypeSchema, FieldSchema
from app.schemas.metadata import (
    ChildTableIntelligence,
    DoctypeIntelligence,
    FieldIntelligence,
    FormLayoutIntelligence,
    SearchIntelligence,
    WorkflowIntelligence,
)
from app.services.erpnext_service import ERPNextService
from app.services.schema_cache import SchemaCache, schema_cache


SEMANTIC_ALIASES: dict[str, list[str]] = {
    "supplier": ["vendor", "seller", "procurement partner", "party"],
    "customer": ["buyer", "client", "client company", "party"],
    "warehouse": ["inventory location", "storage", "store", "location"],
    "company": ["business", "organization", "legal entity"],
    "currency": ["money", "fx", "transaction currency"],
    "item_code": ["item", "product", "sku", "stock item"],
    "qty": ["quantity", "units", "pieces", "pcs", "number"],
    "rate": ["price", "unit price", "cost"],
    "amount": ["value", "line total", "total"],
    "cost_center": ["department", "cost allocation", "dimension"],
    "project": ["job", "work", "initiative"],
    "account": ["ledger", "gl account", "chart of account"],
    "posting_date": ["date", "transaction date"],
    "transaction_date": ["date", "order date"],
}

SEARCH_FIELD_HINTS = {
    "name",
    "title",
    "item_code",
    "item_name",
    "supplier_name",
    "customer_name",
    "warehouse_name",
    "employee_name",
    "project_name",
    "account_name",
    "subject",
}

FIELD_PRIORITY = [
    "item_code",
    "item_name",
    "description",
    "qty",
    "stock_qty",
    "uom",
    "stock_uom",
    "rate",
    "price_list_rate",
    "warehouse",
    "s_warehouse",
    "t_warehouse",
    "schedule_date",
    "delivery_date",
    "amount",
]


class MetadataService:
    """Builds AI-ready DocType intelligence from ERPNext/Frappe metadata."""

    def __init__(self, erp: ERPNextService | None = None, cache: SchemaCache | None = None) -> None:
        self.erp = erp or ERPNextService(FrappeClient(settings.frappe_base_url, settings.frappe_auth_mode, settings.frappe_api_key, settings.frappe_api_secret, settings.frappe_session_cookie_name))
        self.cache = cache or schema_cache

    async def get_doctype_intelligence(self, doctype: str, cookies: dict | None = None, refresh: bool = False) -> DoctypeIntelligence:
        key = f"doctype:{doctype}"
        if not refresh:
            cached = self.cache.get(key)
            if cached:
                return cached
        schema = await self.erp.get_doctype_schema(doctype, cookies)
        intelligence = await self._build(schema, cookies)
        self.cache.set(key, intelligence)
        return intelligence

    async def get_form_layout(self, doctype: str, cookies: dict | None = None) -> FormLayoutIntelligence:
        intelligence = await self.get_doctype_intelligence(doctype, cookies)
        return intelligence.form or FormLayoutIntelligence(fields=intelligence.fields, child_tables=intelligence.child_tables)

    async def _build(self, schema: DoctypeSchema, cookies: dict | None) -> DoctypeIntelligence:
        fields = [self._field(field) for field in schema.fields]
        link_fields = [field for field in fields if field.link_to]
        child_tables = await self._child_tables(fields, cookies)
        mandatory = [field.fieldname for field in fields if field.required and not field.hidden]
        writable = [field.fieldname for field in fields if field.writable and not field.hidden]
        search = self._search(fields)
        form = self._form(fields, child_tables)
        cache_key = hashlib.sha1("|".join(f"{field.fieldname}:{field.fieldtype}:{field.options}:{field.required}:{field.read_only}:{field.hidden}" for field in fields).encode()).hexdigest()[:16]
        return DoctypeIntelligence(
            doctype=schema.doctype,
            module=schema.module,
            title_field=search.title_field,
            is_submittable=schema.is_submittable,
            fields=fields,
            child_tables=child_tables,
            mandatory_fields=mandatory,
            writable_fields=writable,
            link_fields=link_fields,
            search=search,
            workflow=WorkflowIntelligence(is_submittable=schema.is_submittable, workflow_state_field=next((field.fieldname for field in fields if field.fieldname == "workflow_state"), None)),
            permissions=schema.permissions,
            form=form,
            cache_key=cache_key,
            diagnostics={"field_count": len(fields), "child_table_count": len(child_tables), "link_field_count": len(link_fields)},
        )

    async def _child_tables(self, fields: list[FieldIntelligence], cookies: dict | None) -> list[ChildTableIntelligence]:
        output: list[ChildTableIntelligence] = []
        for table_field in [field for field in fields if field.fieldtype == "Table" and field.child_doctype]:
            try:
                child_schema = await self.erp.get_doctype_schema(table_field.child_doctype or "", cookies)
                child_fields = [self._field(field) for field in child_schema.fields]
            except Exception:
                child_fields = []
            editable = [field for field in child_fields if field.writable and not field.hidden]
            links = [field for field in editable if field.link_to]
            ordered = sorted(editable, key=lambda field: FIELD_PRIORITY.index(field.fieldname) if field.fieldname in FIELD_PRIORITY else len(FIELD_PRIORITY))
            output.append(ChildTableIntelligence(fieldname=table_field.fieldname, label=table_field.label, child_doctype=table_field.child_doctype, required=table_field.required, link_fields=links, editable_fields=ordered, required_fields=[field.fieldname for field in child_fields if field.required], field_priority=[field.fieldname for field in ordered]))
        return output

    def _field(self, field: FieldSchema) -> FieldIntelligence:
        fieldtype = field.fieldtype or "Data"
        link_to = field.options if fieldtype in {"Link", "Dynamic Link"} else None
        child_doctype = field.options if fieldtype == "Table" else None
        aliases = self._aliases(field.fieldname, field.label, link_to)
        computed = fieldtype in {"Section Break", "Column Break", "Tab Break", "HTML", "Button"} or field.read_only
        importance = "hidden" if field.hidden else "read_only" if field.read_only else "required" if field.required else "computed" if computed else "optional"
        return FieldIntelligence(
            fieldname=field.fieldname,
            label=field.label or field.fieldname.replace("_", " ").title(),
            fieldtype=fieldtype,
            options=field.options,
            required=field.required,
            read_only=field.read_only,
            hidden=field.hidden,
            permlevel=field.permlevel,
            link_to=link_to,
            child_doctype=child_doctype,
            depends_on=field.depends_on,
            fetch_from=field.fetch_from,
            default=field.default,
            description=field.description,
            aliases=aliases,
            examples=self._examples(field.fieldname, link_to),
            importance=importance,
            writable=not field.read_only and not field.hidden and fieldtype not in {"Section Break", "Column Break", "Tab Break", "HTML", "Button"},
            searchable=field.fieldname in SEARCH_FIELD_HINTS or field.fieldname.endswith(("_name", "_code", "_no", "_number")) or bool(link_to),
        )

    @staticmethod
    def _aliases(fieldname: str, label: str, link_to: str | None) -> list[str]:
        tokens = {fieldname.replace("_", " "), label.lower()}
        tokens.update(SEMANTIC_ALIASES.get(fieldname, []))
        if link_to:
            tokens.update(SEMANTIC_ALIASES.get(link_to.lower().replace(" ", "_"), []))
            tokens.add(link_to.lower())
        return sorted({item.strip() for item in tokens if item and item.strip()})

    @staticmethod
    def _examples(fieldname: str, link_to: str | None) -> list[str]:
        if link_to:
            return [f"select {fieldname.replace('_', ' ')}", f"search {link_to}"]
        if fieldname in {"qty", "rate"}:
            return [f"{fieldname} 1", f"set {fieldname}"]
        return []

    @staticmethod
    def _search(fields: list[FieldIntelligence]) -> SearchIntelligence:
        title_field = next((field.fieldname for field in fields if field.fieldname in SEARCH_FIELD_HINTS and field.fieldname != "name"), None)
        search_fields = ["name", *[field.fieldname for field in fields if field.searchable and field.fieldname != "name"]]
        display_fields = [field for field in search_fields if field][:5]
        return SearchIntelligence(title_field=title_field, search_fields=list(dict.fromkeys(search_fields)), display_fields=display_fields)

    @staticmethod
    def _form(fields: list[FieldIntelligence], child_tables: list[ChildTableIntelligence]) -> FormLayoutIntelligence:
        sections: list[dict[str, Any]] = []
        current = {"title": "Details", "fields": []}
        for field in fields:
            if field.fieldtype in {"Section Break", "Tab Break"}:
                if current["fields"]:
                    sections.append(current)
                current = {"title": field.label, "fields": []}
                continue
            if field.fieldtype != "Column Break" and not field.hidden:
                current["fields"].append(field.fieldname)
        if current["fields"]:
            sections.append(current)
        return FormLayoutIntelligence(sections=sections, fields=[field for field in fields if not field.hidden], child_tables=child_tables)

    async def safe_search_fields(self, doctype: str, cookies: dict | None = None) -> list[str]:
        intelligence = await self.get_doctype_intelligence(doctype, cookies)
        return intelligence.search.search_fields or ["name"]


def normalize_field_text(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", str(value or "").lower()).strip()


metadata_service = MetadataService()
