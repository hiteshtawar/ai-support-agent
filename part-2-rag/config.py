"""Configuration for the Part 2 RAG-backed support agent."""

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# Absolute path to the docs/ folder sitting next to this file.
_DOCS_DIR = str(Path(__file__).parent / "docs")


@dataclass
class Config:
    """All tuneable settings for the RAG support agent in one place.

    Attributes:
        model: Ollama chat model tag used for the agent loop.
        embed_model: Ollama embedding model tag used to build and query the index.
        docs_dir: Path to the directory containing .md documentation files.
        chunk_size: Number of words per chunk when building the index.
        overlap: Word overlap between adjacent chunks.
        top_k: Number of retrieved chunks passed to the model as context.
        max_tokens: Upper bound on tokens in a single chat response.
        temperature: Sampling temperature — lower is more deterministic.
        system_prompt: Instruction block prepended to every conversation.
    """

    model: str = field(default_factory=lambda: os.getenv("OLLAMA_MODEL", "llama3.2"))
    embed_model: str = field(
        default_factory=lambda: os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text")
    )
    docs_dir: str = field(default_factory=lambda: os.getenv("DOCS_DIR", _DOCS_DIR))
    chunk_size: int = 150
    overlap: int = 30
    top_k: int = 3
    max_tokens: int = 1024
    temperature: float = 0.2
    system_prompt: str = (
        "You are a helpful support agent for Sample App, the SaaS product built by Sample Company.\n\n"
        "Rules:\n"
        "1. When the user message starts with [Documentation from ...], that section contains "
        "relevant help content retrieved from the docs. Read it carefully and answer the question "
        "directly from that content. Do not ask for a ticket — just answer.\n"
        "2. After answering, mention the source filename (e.g. 'Source: dashboard.md'). "
        "Do NOT invent URLs or links — only cite the filename.\n"
        "3. If no documentation section is present and you don't know the answer, "
        "offer to create a support ticket.\n"
        "4. Before calling create_ticket, ask the user for their email address if you don't have it.\n"
        "5. Be friendly but brief. Bullet points are fine; walls of text are not.\n"
        "6. Never invent features, settings, or URLs that are not in the provided documentation."
    )


config = Config()
