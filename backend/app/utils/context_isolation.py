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
