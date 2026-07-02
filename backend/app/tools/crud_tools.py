from app.services.crud_service import CrudService, crud_service


class CrudTools:
    def __init__(self, service: CrudService | None = None): self.service=service or crud_service
    async def prepare_create_record(self, **kwargs): return await self.service.prepare_create(**kwargs)
    async def prepare_update_record(self, **kwargs): return await self.service.prepare_update(**kwargs)
    async def confirm_crud_action(self, confirmation_id: str, cookies: dict | None = None, user: str = "unknown"): return await self.service.confirm(confirmation_id,cookies,user)
    async def cancel_crud_action(self, confirmation_id: str, user: str = "unknown"): return await self.service.cancel(confirmation_id,user)
