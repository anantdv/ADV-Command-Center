from typing import Any

from app.frappe.client import FrappeClient
from app.frappe import paths


async def call(client:FrappeClient,path:str,payload:dict[str,Any]|None,cookies:dict|None,method:str="post") -> dict:
    if method=="get": return await client.get(path,params=payload,cookies=cookies)
    return await client.post(path,payload,cookies=cookies)
