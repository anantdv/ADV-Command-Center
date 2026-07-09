from app.schemas.modules import ERPModule
from app.services.erpnext_service import ERPNextService
from app.utils.module_registry import MODULE_REGISTRY


class ModulePermissionBuilder:
    def __init__(self, erp: ERPNextService):
        self.erp = erp

    async def get_accessible_modules(self, cookies: dict | None = None) -> list[ERPModule]:
        allowed = await self.erp.get_allowed_doctypes(cookies=cookies)
        allowed_names = {item.name for item in allowed}
        modules: list[ERPModule] = []
        for module_name, config in MODULE_REGISTRY.items():
            doctypes = [doctype for doctype in config["doctypes"] if doctype in allowed_names]
            if not doctypes:
                continue
            modules.append(
                ERPModule(
                    module_name=module_name,
                    label=config["label"],
                    icon=config.get("icon"),
                    description=config.get("description"),
                    category=config.get("category"),
                    route=config["route"],
                    accessible=True,
                    doctypes=doctypes,
                )
            )
        return modules
