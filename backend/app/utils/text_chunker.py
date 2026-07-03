import re


def chunk_text(text: str, chunk_size: int = 900, overlap: int = 150, max_chunks: int = 2000) -> list[str]:
    """Chunk normalized text while preferring paragraph boundaries."""
    if chunk_size < 100:
        raise ValueError("chunk_size must be at least 100 characters")
    overlap = min(max(overlap, 0), chunk_size // 2)
    normalized = re.sub(r"[ \t]+", " ", text.replace("\x00", " "))
    paragraphs = [part.strip() for part in re.split(r"\n\s*\n+", normalized) if part.strip()]
    if not paragraphs:
        return []
    chunks: list[str] = []
    current = ""
    for paragraph in paragraphs:
        pieces = [paragraph[i:i + chunk_size] for i in range(0, len(paragraph), chunk_size)] or [paragraph]
        for piece in pieces:
            candidate = f"{current}\n\n{piece}".strip() if current else piece
            if len(candidate) <= chunk_size:
                current = candidate
                continue
            if current:
                chunks.append(current.strip())
                if len(chunks) >= max_chunks:
                    return chunks
                prefix = current[-overlap:] if overlap else ""
                current = f"{prefix}\n\n{piece}".strip()
            else:
                current = piece
    if current.strip() and len(chunks) < max_chunks:
        chunks.append(current.strip())
    return [item for item in chunks if item]
