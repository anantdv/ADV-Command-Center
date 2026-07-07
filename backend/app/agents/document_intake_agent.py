from app.services.document_intake_service import DocumentIntakeService, document_intake_service


class DocumentIntakeAgent:
    def __init__(self, service: DocumentIntakeService | None = None):
        self.service = service or document_intake_service
