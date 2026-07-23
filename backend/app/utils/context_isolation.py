from __future__ import annotations

import re

CONTEXT_REFERENCE_PHRASES = [
    "this record",
    "this invoice",
    "this customer",
    "selected row",
    "above result",
    "these records",
    "selected",
    "above",
    "these",
    "them",
    "this",
    "it",
]


CONTEXTUAL_WORKFLOW_REFERENCES = (
    "approve it",
    "reject it",
    "approve this",
    "reject this",
    "approve this document",
    "reject this document",
    "send it back",
    "send this back",
    "process it",
    "process this",
    "take action on this",
    "apply this action",
)


def has_explicit_context_reference(message: str) -> bool:
    text = f" {' '.join(message.lower().split())} "
    if re.search(r"\b(?:this|that|selected|above|these|them|it)\b", text):
        return True
    return any(f" {phrase} " in text for phrase in CONTEXT_REFERENCE_PHRASES)


def should_use_previous_context(message: str) -> bool:
    text = " ".join(message.lower().split())
    if not has_explicit_context_reference(text):
        return False
    independent_patterns = (
        r"\bshow\s+(?:stock balance|stock|customers|invoices|sales invoices|payables|receivables)\b",
        r"\b(?:generate|show)\s+(?:sales|purchase|stock|customer|invoice).*(?:chart|trend)\b",
        r"\bshow\s+(?:top customers|monthly sales|unpaid invoices)\b",
    )
    return not any(re.search(pattern, text) for pattern in independent_patterns)


def is_contextual_workflow_reference(message: str) -> bool:
    text = " ".join(message.lower().split())
    if any(phrase in text for phrase in CONTEXTUAL_WORKFLOW_REFERENCES):
        return True
    return bool(re.search(r"\b(approve|reject|process|return)\s+(it|this|this document|document)\b", text))


def should_use_workflow_context(message: str) -> bool:
    text = " ".join(message.lower().split())
    if re.search(r"\b(show|list|create|draft|export|generate|stock|customers?|suppliers?|items?|receivables?|payables?)\b", text):
        return is_contextual_workflow_reference(text)
    return is_contextual_workflow_reference(text)
