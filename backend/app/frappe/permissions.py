from app.frappe.client import FrappeClient
from app.frappe.paths import CHECK_PERMISSION, GET_ALLOWED_DOCTYPES


async def get_allowed_doctypes(client: FrappeClient, module: str | None, cookies: dict | None) -> dict:
    params = {"module": module} if module else None
    return await client.get(GET_ALLOWED_DOCTYPES, params=params, cookies=cookies)


async def check_permission(client: FrappeClient, payload: dict, cookies: dict | None) -> dict:
    return await client.post(CHECK_PERMISSION, payload, cookies=cookies)
