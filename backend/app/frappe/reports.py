from app.frappe.client import FrappeClient
from app.frappe.paths import GET_ALLOWED_REPORTS, RUN_REPORT


async def get_allowed_reports(client: FrappeClient, module: str | None, cookies: dict | None) -> dict:
    params = {"module": module} if module else None
    return await client.get(GET_ALLOWED_REPORTS, params=params, cookies=cookies)


async def run_report(client: FrappeClient, report_name: str, filters: dict, cookies: dict | None) -> dict:
    return await client.post(
        RUN_REPORT,
        {"report_name": report_name, "filters": filters},
        cookies=cookies,
    )
