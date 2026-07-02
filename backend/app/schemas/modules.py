from typing import Any

from app.schemas.common import CamelModel, PermissionMeta


class ModuleSummary(CamelModel):
    slug: str
    name: str
    description: str
    metric: str
    metric_label: str
    color: str
    permissions: PermissionMeta


class ModuleDetail(CamelModel):
    module: ModuleSummary
    records: list[str]
    reports: list[str]


class ModuleRecords(CamelModel):
    records: list[dict[str, Any]]
    permissions: PermissionMeta


class ModuleReports(CamelModel):
    reports: list[str]
    permissions: PermissionMeta
