from app.services.document_intake_service import DocumentIntakeService, document_intake_service


class DocumentIntakeTools:
    def __init__(self, service: DocumentIntakeService | None = None):
        self.service = service or document_intake_service
