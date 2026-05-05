"""Tool handler functions for the Part 2 RAG-backed support agent."""

import uuid
from datetime import datetime, timezone

from config import Config, config as default_config
from rag import Chunk, build_index, search_index

# In-memory ticket store — resets on each run.
_ticket_store: dict[str, dict] = {}

_DEMO_STATUSES: list[str] = [
    "open",
    "in_progress",
    "waiting_on_customer",
    "resolved",
]

# The RAG index is built once at startup and cached here.
# None means it has not been built yet (lazy initialisation).
_index: list[Chunk] | None = None


def _get_index(cfg: Config) -> list[Chunk]:
    """Return the cached index, building it on first call.

    Building embeds every chunk in the docs/ folder, which requires Ollama
    to be running.  Subsequent calls return the cached list immediately.

    Args:
        cfg: Config instance supplying docs_dir, embed_model, chunk_size, overlap.

    Returns:
        The populated list of Chunk objects.
    """
    global _index
    if _index is None:
        print("  Building RAG index… (this runs once at startup)")
        _index = build_index(cfg.docs_dir, cfg.embed_model)
        print(f"  Index ready — {len(_index)} chunks from {cfg.docs_dir}")
    return _index


def reset_index() -> None:
    """Clear the cached index so the next call to _get_index rebuilds it.

    Used in tests to ensure a clean state between test cases.
    """
    global _index
    _index = None


def search_docs(query: str) -> dict:
    """Search the Sample App documentation using semantic similarity.

    Embeds the query, scores every chunk in the index by cosine similarity,
    and returns the top results concatenated into a single context string.

    Args:
        query: The user's natural-language question.

    Returns:
        A dict with keys ``found`` (bool), ``answer`` (str), and ``sources``
        (list of source filenames).  When nothing is relevant, ``found`` is
        False.
    """
    if not isinstance(query, str):
        query = str(query)
    if not query.strip():
        return {
            "found": False,
            "answer": "I couldn't understand your question. Could you rephrase it?",
            "sources": [],
        }

    results = search_index(
        query=query,
        index=_get_index(default_config),
        embed_model=default_config.embed_model,
        top_k=default_config.top_k,
    )

    # Treat a top score below 0.25 as "not found".
    # nomic-embed-text scores typically range 0.3–0.8 for relevant content;
    # 0.25 catches genuine misses without being too aggressive.
    if not results or results[0]["score"] < 0.25:
        return {
            "found": False,
            "answer": (
                "I don't have a help article that covers your question. "
                "I can create a support ticket so a human agent can assist you."
            ),
            "sources": [],
        }

    context = "\n\n---\n\n".join(r["text"] for r in results)
    sources = list({r["source"] for r in results})

    return {
        "found": True,
        "answer": context,
        "sources": sources,
    }


def create_ticket(issue: str, user_email: str) -> dict:
    """Create a fake support ticket and store it in the in-memory ticket store.

    Args:
        issue: A brief description of the user's problem.
        user_email: The user's email address for follow-up.

    Returns:
        A dict with ``ticket_id``, ``issue``, ``user_email``, ``status``,
        and ``created_at`` (ISO-8601 UTC string).
    """
    ticket_id = f"TKT-{uuid.uuid4().hex[:6].upper()}"
    ticket = {
        "ticket_id": ticket_id,
        "issue": issue,
        "user_email": user_email,
        "status": "open",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    _ticket_store[ticket_id] = ticket
    return ticket


def get_ticket_status(ticket_id: str) -> dict:
    """Return the current status of a support ticket.

    Checks the in-memory store first.  Falls back to a deterministic demo
    status for unknown IDs.

    Args:
        ticket_id: The ticket identifier, e.g. ``"TKT-A1B2C3"``.

    Returns:
        A dict with keys ``ticket_id``, ``status``, and ``message``.
    """
    normalized = ticket_id.strip().upper()

    if normalized in _ticket_store:
        ticket = _ticket_store[normalized]
        return {
            "ticket_id": normalized,
            "status": ticket["status"],
            "message": f"Ticket {normalized} is currently '{ticket['status']}'.",
        }

    index = sum(ord(c) for c in normalized) % len(_DEMO_STATUSES)
    demo_status = _DEMO_STATUSES[index]
    return {
        "ticket_id": normalized,
        "status": demo_status,
        "message": (
            f"Ticket {normalized} is currently '{demo_status}'. "
            "(Note: this ticket was not created in the current session.)"
        ),
    }


TOOL_DEFINITIONS: list[dict] = [
    {
        "type": "function",
        "function": {
            "name": "search_docs",
            "description": (
                "Search the Sample App documentation for an answer to the user's question. "
                "Uses semantic similarity — call this for any how-to or troubleshooting question."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The user's question or issue description.",
                    }
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_ticket",
            "description": (
                "Create a support ticket when the docs have no answer or the user requests one. "
                "Always confirm with the user before calling this."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "issue": {
                        "type": "string",
                        "description": "A concise description of the user's problem.",
                    },
                    "user_email": {
                        "type": "string",
                        "description": "The user's email address for follow-up.",
                    },
                },
                "required": ["issue", "user_email"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_ticket_status",
            "description": "Look up the current status of an existing support ticket by its ID.",
            "parameters": {
                "type": "object",
                "properties": {
                    "ticket_id": {
                        "type": "string",
                        "description": "The ticket ID, e.g. TKT-A1B2C3.",
                    }
                },
                "required": ["ticket_id"],
            },
        },
    },
]

TOOL_HANDLERS: dict[str, callable] = {
    "search_docs": search_docs,
    "create_ticket": create_ticket,
    "get_ticket_status": get_ticket_status,
}
