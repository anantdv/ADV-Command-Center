from __future__ import annotations


def classify_document_type(text: str) -> str:
    lowered = text.lower()
    if any(term in lowered for term in ("tax invoice", "invoice no", "invoice number", "supplier invoice")):
        return "supplier_invoice"
    if any(term in lowered for term in ("purchase order", "po no", "po number", "buyer")):
        return "customer_purchase_order"
    if "quotation" in lowered or "quote no" in lowered:
        if any(term in lowered for term in ("supplier", "vendor")):
            return "supplier_quotation"
        return "customer_request_for_quotation"
    if "delivery note" in lowered or "delivered to" in lowered:
        return "delivery_document"
    if "goods receipt" in lowered or "purchase receipt" in lowered or "received" in lowered:
        return "goods_receipt_document"
    return "unknown"
