from app.frappe.client import FrappeClient
from app.frappe.paths import GET_CURRENT_USER_CONTEXT


async def get_current_user_context(client: FrappeClient, cookies: dict | None) -> dict:
    return await client.get(GET_CURRENT_USER_CONTEXT, cookies=cookies)
