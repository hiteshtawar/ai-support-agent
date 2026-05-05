"""RAG pipeline: chunking, embedding, and semantic retrieval for Sample App docs."""

import math
from dataclasses import dataclass, field
from pathlib import Path

import ollama


@dataclass
class Chunk:
    """A single text chunk with its source filename and embedding vector."""

    text: str
    source: str
    embedding: list[float] = field(default_factory=list)


def chunk_text(
    text: str, source: str, chunk_size: int = 150, overlap: int = 30
) -> list[Chunk]:
    """Split a document into overlapping word-window chunks.

    Overlap ensures that a sentence split across a boundary is still
    fully represented in at least one chunk.

    Args:
        text: The full document text.
        source: Filename or identifier used for provenance in search results.
        chunk_size: Number of words per chunk.
        overlap: Number of words repeated at the start of the next chunk.

    Returns:
        List of Chunk objects without embeddings (embeddings added later).
    """
    words = text.split()
    chunks: list[Chunk] = []
    step = chunk_size - overlap
    for i in range(0, len(words), step):
        chunk_words = words[i : i + chunk_size]
        if not chunk_words:
            break
        chunks.append(Chunk(text=" ".join(chunk_words), source=source))
    return chunks


def embed_text(text: str, model: str) -> list[float]:
    """Return the embedding vector for a text string using Ollama.

    Args:
        text: The text to embed.
        model: The Ollama embedding model tag, e.g. ``"nomic-embed-text"``.

    Returns:
        A list of floats representing the embedding vector.
    """
    response = ollama.embeddings(model=model, prompt=text)
    return response["embedding"]


def cosine_similarity(a: list[float], b: list[float]) -> float:
    """Compute cosine similarity between two embedding vectors.

    Returns a value between -1.0 and 1.0. Higher is more similar.
    Returns 0.0 if either vector is all zeros.

    Args:
        a: First embedding vector.
        b: Second embedding vector.

    Returns:
        Cosine similarity score.
    """
    dot = sum(x * y for x, y in zip(a, b))
    mag_a = math.sqrt(sum(x * x for x in a))
    mag_b = math.sqrt(sum(x * x for x in b))
    if mag_a == 0.0 or mag_b == 0.0:
        return 0.0
    return dot / (mag_a * mag_b)


def load_docs(docs_dir: str) -> list[tuple[str, str]]:
    """Read all .md files in docs_dir and return (filename, content) pairs.

    Args:
        docs_dir: Path to the directory containing markdown documentation files.

    Returns:
        List of (filename, text_content) tuples sorted by filename for
        deterministic ordering.
    """
    docs_path = Path(docs_dir)
    results: list[tuple[str, str]] = []
    for md_file in sorted(docs_path.glob("*.md")):
        results.append((md_file.name, md_file.read_text(encoding="utf-8")))
    return results


def build_index(docs_dir: str, embed_model: str) -> list[Chunk]:
    """Load all docs, chunk them, embed each chunk, and return the index.

    This is the offline (or startup-time) phase of the RAG pipeline.
    The index is a plain list of Chunk objects held in memory.

    Args:
        docs_dir: Path to the directory containing .md documentation files.
        embed_model: Ollama embedding model tag to use for all chunks.

    Returns:
        List of Chunk objects with embeddings populated.
    """
    docs = load_docs(docs_dir)
    index: list[Chunk] = []
    for filename, content in docs:
        chunks = chunk_text(content, source=filename)
        for chunk in chunks:
            chunk.embedding = embed_text(chunk.text, embed_model)
            index.append(chunk)
    return index


def search_index(
    query: str,
    index: list[Chunk],
    embed_model: str,
    top_k: int = 3,
) -> list[dict]:
    """Embed the query and return the top_k most similar chunks.

    This is the online (per-query) phase of the RAG pipeline.

    Args:
        query: The user's natural-language question.
        index: Pre-built list of Chunk objects (from build_index).
        embed_model: Ollama embedding model tag — must match the one used
            to build the index.
        top_k: Number of results to return.

    Returns:
        List of dicts with keys ``text``, ``source``, and ``score``,
        sorted by score descending.
    """
    if not index:
        return []

    query_embedding = embed_text(query, embed_model)
    scored = [
        {
            "text": chunk.text,
            "source": chunk.source,
            "score": cosine_similarity(query_embedding, chunk.embedding),
        }
        for chunk in index
    ]
    scored.sort(key=lambda r: r["score"], reverse=True)
    return scored[:top_k]
