import re
from typing import Any


class PayloadBuilder:
    """Deterministic first-pass extraction. TODO: replace with validated structured LLM extraction."""
    FIELD_PATTERNS = {
        "customer_group": r"customer group\s+(?:is\s+)?(.+?)(?=\s+and\s+|$)", "supplier_group": r"supplier group\s+(?:is\s+)?(.+?)(?=\s+and\s+|$)",
        "item_group": r"item group\s+(?:is\s+)?(.+?)(?=\s+and\s+|$)", "stock_uom": r"stock uom\s+(?:is\s+)?(.+?)(?=\s+and\s+|$)",
        "territory": r"territory\s+(?:is\s+|to\s+)?(.+?)(?=\s+and\s+|$)", "country": r"country\s+(?:is\s+|to\s+)?(.+?)(?=\s+and\s+|$)",
        "mobile_no": r"mobile(?: number| no)?\s+(?:is\s+|to\s+)?([+\d][\d -]+)", "email_id": r"email\s+(?:is\s+|to\s+)?([^\s,]+@[^\s,]+)",
        "description": r"description\s+(?:is\s+|to\s+)?(.+)$", "status": r"status\s+(?:is\s+|to\s+)?(.+?)(?=\s+and\s+|$)",
        "valid_till": r"valid till\s+(?:is\s+|to\s+)?([^,]+?)(?=\s+and\s+|$)", "priority": r"priority\s+(?:is\s+|to\s+)?(.+?)(?=\s+and\s+|$)",
    }

    @classmethod
    def extract_create(cls, doctype: str, prompt: str) -> dict[str, Any]:
        text = " ".join(prompt.strip().split());lower=text.lower();data:dict[str,Any]={}
        alias = "support ticket" if "support ticket" in lower else doctype.lower()
        tail = re.split(rf"\b(?:create|add)\s+(?:a\s+)?{re.escape(alias)}\b", text, maxsplit=1, flags=re.I)[-1].strip()
        base = re.split(r"\s+with\s+", tail, maxsplit=1, flags=re.I)[0].strip()
        if doctype == "Customer": data["customer_name"] = base
        elif doctype == "Supplier": data["supplier_name"] = base
        elif doctype == "Item":
            match=re.match(r"([^\s]+)(?:\s+called\s+(.+?))?(?=\s+with\s+|$)",tail,re.I)
            if match: data.update({"item_code":match.group(1),"item_name":match.group(2) or match.group(1)})
        elif doctype == "Lead":
            match=re.match(r"(?:for\s+)?(.+?)(?:\s+from\s+(.+?))?(?=\s+with\s+|$)",base,re.I)
            if match: data["lead_name"]=match.group(1).strip();data.update({"company_name":match.group(2).strip()} if match.group(2) else {})
        elif doctype == "Issue": data.update({"subject":base,"description":base})
        elif doctype == "Quotation":
            party=re.sub(r"^(?:for\s+)?(?:customer\s+)?","",base,flags=re.I).strip();data.update({"quotation_to":"Customer","party_name":party})
        elif doctype == "Opportunity":
            party=re.sub(r"^(?:for\s+)?(?:customer\s+)?","",base,flags=re.I).strip();data.update({"opportunity_from":"Customer","party_name":party})
        elif doctype in {"Sales Order", "Sales Invoice", "Delivery Note"}:
            party = cls._party_after(lower, text, "customer")
            if party: data["customer"] = party
        elif doctype in {"Purchase Order", "Purchase Invoice", "Purchase Receipt"}:
            party = cls._party_after(lower, text, "supplier")
            if party: data["supplier"] = party
        elif doctype == "Material Request":
            data["material_request_type"] = "Purchase"
        elif doctype == "Project":
            data["project_name"] = base
        elif doctype == "Task":
            data["subject"] = base
        cls._extract_items(text, data)
        cls._extract_document_refs(text, data)
        cls._extract_fields(text,data)
        return {key:value.strip() if isinstance(value,str) else value for key,value in data.items() if value not in (None,"")}

    @classmethod
    def extract_update(cls, doctype: str, prompt: str) -> tuple[str | None, dict[str, Any]]:
        field_aliases = r"territory|mobile(?: number| no)?|email|description|status|customer group|supplier group|item group|stock uom|valid till|priority|docstatus|owner|company"
        alias = doctype.lower()
        match=re.search(rf"\b(?:update|change)\s+{re.escape(alias)}\s+(.+?)\s+({field_aliases})\s+(?:to\s+|is\s+)?(.+)$",prompt,re.I)
        if not match: return None,{}
        record_name=match.group(1).strip();phrase=match.group(2).lower();value=match.group(3).strip()
        mapping={"mobile number":"mobile_no","mobile no":"mobile_no","email":"email_id","customer group":"customer_group","supplier group":"supplier_group","item group":"item_group","stock uom":"stock_uom","valid till":"valid_till"}
        return record_name,{mapping.get(phrase,phrase.replace(" ","_")):value}

    @classmethod
    def _extract_fields(cls,text:str,data:dict[str,Any])->None:
        for field,pattern in cls.FIELD_PATTERNS.items():
            match=re.search(pattern,text,re.I)
            if match: data[field]=match.group(1).strip()

    @staticmethod
    def _party_after(lower: str, text: str, keyword: str) -> str | None:
        match = re.search(rf"\b{keyword}\s+(.+?)(?=\s+(?:for|with|bill number|po number|containing|items?)\b|$)", text, re.I)
        if match:
            return match.group(1).strip()
        if f" for " in lower:
            tail = re.split(r"\bfor\b", text, maxsplit=1, flags=re.I)[-1]
            tail = re.split(r"\b(?:with|containing|items?)\b", tail, maxsplit=1, flags=re.I)[0]
            return re.sub(rf"^(?:{keyword}\s+)?", "", tail.strip(), flags=re.I).strip() or None
        return None

    @staticmethod
    def _extract_items(text: str, data: dict[str, Any]) -> None:
        matches = re.findall(
            r"(?:(\d+(?:\.\d+)?)\s+)?((?:ITEM|item)[-\w]+)(?:\s+(?:at|@)\s+([\d,.]+))?",
            text,
            re.I,
        )
        if not matches:
            return
        items = []
        for qty, code, rate in matches:
            q = float(qty) if qty else 1
            r = float(rate.replace(",", "")) if rate else 0
            items.append({"item_code": code.upper(), "qty": q, "rate": r, "amount": q * r})
        data["items"] = items

    @staticmethod
    def _extract_document_refs(text: str, data: dict[str, Any]) -> None:
        refs = {
            "bill_no": r"bill (?:number|no)\s+([A-Z0-9-]+)",
            "po_no": r"po (?:number|no)\s+([A-Z0-9-]+)",
            "currency": r"currency\s+([A-Z]{3})",
        }
        for field, pattern in refs.items():
            match = re.search(pattern, text, re.I)
            if match:
                data[field] = match.group(1).strip().upper()
