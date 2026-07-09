from typing import Any

from app.frappe.client import FrappeClient
from app.frappe.paths import CREATE_RECORD, GET_DOCUMENT_DETAIL, GET_RECORD, LIST_RECORDS, UPDATE_RECORD


async def list_records(client: FrappeClient, payload: dict[str, Any], cookies: dict | None) -> dict:
    return await client.post(LIST_RECORDS, payload, cookies=cookies)


async def get_record(client: FrappeClient, payload: dict[str, Any], cookies: dict | None) -> dict:
    return await client.post(GET_RECORD, payload, cookies=cookies)


async def get_document_detail(client: FrappeClient, payload: dict[str, Any], cookies: dict | None) -> dict:
    return await client.post(GET_DOCUMENT_DETAIL, payload, cookies=cookies)


async def create_record(client: FrappeClient, payload: dict[str, Any], cookies: dict | None) -> dict:
    return await client.post(CREATE_RECORD, payload, cookies=cookies)


async def update_record(client: FrappeClient, payload: dict[str, Any], cookies: dict | None) -> dict:
    return await client.post(UPDATE_RECORD, payload, cookies=cookies)
