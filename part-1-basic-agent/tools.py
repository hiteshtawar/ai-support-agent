"""Tool handler functions for the Sample Company support agent."""

import uuid
from datetime import datetime, timezone

from faq import FAQ_ENTRIES

# Fake ticket store — resets on each run, which is fine for teaching purposes.
_ticket_store: dict[str, dict] = {}

# Hardcoded statuses cycled through so demo conversations feel realistic.
_DEMO_STATUSES: list[str] = [
    "open",
    "in_progress",
    "waiting_on_customer",
    "resolved",
]


def search_faq(query: str) -> dict:
    """Search the hardcoded FAQ for the best match to the user's query.

    Matching strategy: count how many of a FAQ entry's keywords appear in the
    lowercased query string.  The entry with the highest hit count wins.  Ties
    go to the entry with the lower id (i.e. the first one defined).

    Args:
        query: The user's natural-language question or complaint.

    Returns:
        A dict with keys ``found`` (bool), ``question``, and ``answer``.
        When nothing matches, ``found`` is False and ``answer`` is a short
        message directing the user to open a ticket.
    """
    if not isinstance(query, str):
        query = str(query)
    if not query or not query.strip():
        return {
            "found": False,
            "question": None,
            "answer": "I couldn't understand your question. Could you rephrase it?",
        }

    lowered = query.lower()
    best_entry: dict | None = None
    best_score = 0

    for entry in FAQ_ENTRIES:
        score = sum(1 for kw in entry["keywords"] if kw in lowered)
        if score > best_score:
            best_score = score
            best_entry = entry

    if best_entry is None or best_score == 0:
        return {
            "found": False,
            "question": None,
            "answer": (
                "I don't have a help article that matches your question. "
                "I can create a support ticket so a human agent can assist you."
            ),
        }

    return {
        "found": True,
        "question": best_entry["question"],
        "answer": best_entry["answer"],
    }


def create_ticket(issue: str, user_email: str) -> dict:
    """Create a fake support ticket and store it in the in-memory ticket store.

    Args:
        issue: A brief description of the user's problem.
        user_email: The user's email address for follow-up.

    Returns:
        A dict containing ``ticket_id``, ``issue``, ``user_email``,
        ``status``, and ``created_at`` (ISO-8601 UTC string).
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

    Checks the in-memory store first (for tickets created in this session).
    Falls back to a deterministic demo status for unknown IDs so the agent
    can still give a sensible answer during demos.

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

    # For unknown IDs, derive a demo status from the ticket ID string so the
    # same ID always returns the same status within a session.
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


# Tool definitions formatted for the Ollama tools API.
TOOL_DEFINITIONS: list[dict] = [
    {
        "type": "function",
        "function": {
            "name": "search_faq",
            "description": (
                "Search the Sample App help documentation for an answer to the user's question. "
                "Use this first before offering to create a ticket."
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
                "Create a support ticket when the FAQ has no answer or the user explicitly requests one. "
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

# Maps tool name strings to their handler functions for fast dispatch.
TOOL_HANDLERS: dict[str, callable] = {
    "search_faq": search_faq,
    "create_ticket": create_ticket,
    "get_ticket_status": get_ticket_status,
}
