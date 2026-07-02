from app.frappe.client import FrappeClient
from app.frappe.paths import GET_DOCTYPE_SCHEMA


async def get_doctype_schema(client: FrappeClient, doctype: str, cookies: dict | None) -> dict:
    return await client.post(GET_DOCTYPE_SCHEMA, {"doctype": doctype}, cookies=cookies)
