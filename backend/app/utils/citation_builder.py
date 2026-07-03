from app.schemas.knowledge import KnowledgeSearchResult, RAGCitation


def build_citations(results: list[KnowledgeSearchResult]) -> list[RAGCitation]:
    return [RAGCitation(citation_id=f"C{i}", source_id=item.source_id, title=item.title, citation_label=item.citation_label, snippet=item.snippet, source_type=item.source_type) for i, item in enumerate(results, 1)]
