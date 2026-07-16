from typing import Any, Literal

from pydantic import BaseModel, Field


UploadedDocumentType = Literal["supplier_invoice", "customer_purchase_order", "supplier_quotation", "customer_request_for_quotation", "delivery_document", "goods_receipt_document", "unknown"]
TargetERPDocumentType = Literal["Purchase Invoice", "Sales Order", "Purchase Order", "Quotation", "Delivery Note", "Purchase Receipt", "Material Request"]


class DocumentUploadResponse(BaseModel):
    intake_id: str
    file_id: str
    file_name: str
    mime_type: str
    status: Literal["uploaded", "processing", "processed", "failed"]
    message: str


class OCRResult(BaseModel):
    intake_id: str
    extracted_text_preview: str
    full_text_available: bool = False
    confidence: float | None = None
    page_count: int | None = None


class ExtractedLineItem(BaseModel):
    item_code: str | None = None
    item_name: str | None = None
    description: str | None = None
    qty: float | None = None
    uom: str | None = None
    rate: float | None = None
    amount: float | None = None
    confidence: float = 0.0
    candidates: list[dict[str, Any]] = Field(default_factory=list)
    warning: str | None = None


class ExtractedDocumentFields(BaseModel):
    source_document_type: UploadedDocumentType
    target_doctype: TargetERPDocumentType | None = None
    supplier: str | None = None
    customer: str | None = None
    bill_no: str | None = None
    bill_date: str | None = None
    po_no: str | None = None
    po_date: str | None = None
    posting_date: str | None = None
    due_date: str | None = None
    currency: str | None = None
    grand_total: float | None = None
    tax_amount: float | None = None
    items: list[ExtractedLineItem] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class FieldExtraction(BaseModel):
    fieldname: str
    label: str
    value: Any | None = None
    confidence: float = 0.0
    candidates: list[dict[str, Any]] = Field(default_factory=list)
    required: bool = False
    warning: str | None = None


class DocumentMappingPreview(BaseModel):
    intake_id: str
    source_document_type: UploadedDocumentType
    target_doctype: TargetERPDocumentType
    extracted_fields: ExtractedDocumentFields
    field_extractions: list[FieldExtraction] = Field(default_factory=list)
    draft_payload: dict[str, Any]
    missing_fields: list[dict[str, Any]] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    raw_text_preview: str | None = None
    confidence: float | None = None
    valid: bool = False
    invalid_reason: str | None = None
    confirmation_required: bool = True
    confirmation_id: str | None = None


class UpdateMappingPreviewRequest(BaseModel):
    target_doctype: TargetERPDocumentType
    draft_payload: dict[str, Any]
