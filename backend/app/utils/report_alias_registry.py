from __future__ import annotations

import re
from typing import Any

REPORT_ALIASES: dict[str, dict[str, Any]] = {
    "stock balance": {
        "intent": "run_report",
        "report_name": "Stock Balance",
        "module_context": "Stock",
        "aliases": ["stock balance", "show stock balance", "show stock", "stock report", "item stock", "show item stock", "current stock", "warehouse stock"],
    },
    "stock ledger": {
        "intent": "run_report",
        "report_name": "Stock Ledger",
        "module_context": "Stock",
        "aliases": ["stock ledger", "stock movement", "item movement", "inventory movement"],
    },
    "accounts receivable": {
        "intent": "run_report",
        "report_name": "Accounts Receivable",
        "module_context": "Accounts",
        "aliases": ["receivables", "accounts receivable", "customer outstanding", "outstanding receivable", "show receivables"],
    },
    "accounts payable": {
        "intent": "run_report",
        "report_name": "Accounts Payable",
        "module_context": "Accounts",
        "aliases": ["payables", "accounts payable", "supplier outstanding", "outstanding payable", "show payables"],
    },
    "general ledger": {
        "intent": "run_report",
        "report_name": "General Ledger",
        "module_context": "Accounts",
        "aliases": ["general ledger", "gl", "ledger", "show ledger"],
    },
    "trial balance": {
        "intent": "run_report",
        "report_name": "Trial Balance",
        "module_context": "Accounts",
        "aliases": ["trial balance", "tb"],
    },
    "sales register": {
        "intent": "run_report",
        "report_name": "Sales Register",
        "module_context": "Selling",
        "aliases": ["sales register", "sales invoice register"],
    },
    "purchase register": {
        "intent": "run_report",
        "report_name": "Purchase Register",
        "module_context": "Buying",
        "aliases": ["purchase register", "purchase invoice register"],
    },
}


def resolve_report_alias(message: str, module_context: str | None = None) -> dict[str, Any] | None:
    text = " ".join(message.lower().split())
    candidates: list[tuple[int, dict[str, Any]]] = []
    for entry in REPORT_ALIASES.values():
        if module_context and entry.get("module_context") and module_context.lower() not in {str(entry["module_context"]).lower(), "accounts" if entry["module_context"] == "Accounts" else str(entry["module_context"]).lower()}:
            # Do not discard exact phrase matches across modules; only lower priority.
            module_penalty = 1
        else:
            module_penalty = 0
        for alias in entry["aliases"]:
            pattern = rf"\b{re.escape(alias)}\b"
            if re.search(pattern, text):
                candidates.append((len(alias) - module_penalty, entry))
    if not candidates:
        return None
    return dict(sorted(candidates, key=lambda item: item[0], reverse=True)[0][1])
