from __future__ import annotations

from app.schemas.analytics_catalog import AnalyticsDefinition
from app.utils.module_analytics_registry import ANALYTICS_CATALOG


class AnalyticsCatalogService:
    def list_catalog(self, module: str | None = None) -> list[AnalyticsDefinition]:
        normalized = _normalize_module(module)
        definitions = [AnalyticsDefinition(**definition) for definition in ANALYTICS_CATALOG.values()]
        if normalized:
            definitions = [definition for definition in definitions if _normalize_module(definition.module) == normalized]
        return sorted(definitions, key=lambda definition: (definition.module, definition.title))

    def get_definition(self, analytics_key: str) -> AnalyticsDefinition:
        return AnalyticsDefinition(**ANALYTICS_CATALOG[analytics_key])

    async def list_accessible_catalog(self, module: str | None, cookies: dict | None = None) -> list[AnalyticsDefinition]:
        # Permission is enforced again at execution time through ERPNext/Frappe APIs.
        # This first version returns configured definitions so module dashboards remain
        # fast and resilient even when one DocType/report is unavailable.
        return self.list_catalog(module)


def _normalize_module(module: str | None) -> str | None:
    if not module:
        return None
    aliases = {"accounting": "accounts", "account": "accounts"}
    value = module.strip().lower()
    return aliases.get(value, value)


analytics_catalog_service = AnalyticsCatalogService()
