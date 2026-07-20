from enum import Enum


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class Intent(str, Enum):
    GENERAL_QUESTION = "general_question"
    ERP_QUERY = "erp_query"
    CRUD_CREATE = "crud_create"
    CRUD_UPDATE = "crud_update"
    REPORT = "report"
    CHART = "chart"
    PREDICTION = "prediction"
    TRAINING = "training"
    SUPPORT = "support"
    DANGEROUS_ACTION = "dangerous_action"
