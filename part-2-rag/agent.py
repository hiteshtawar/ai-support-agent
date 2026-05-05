"""Main agent loop for the Part 2 RAG-backed support agent."""

import json
import re
import shutil

import ollama

from config import Config, config as default_config
from tools import TOOL_DEFINITIONS, TOOL_HANDLERS, search_docs

# search_docs is handled via pre-retrieval before every LLM call — the LLM
# only needs tools for actions the user explicitly requests.
_ACTION_TOOL_DEFINITIONS = [
    t for t in TOOL_DEFINITIONS if t["function"]["name"] != "search_docs"
]

_RESET = "\033[0m"
_BOLD = "\033[1m"
_DIM = "\033[2m"
_CYAN = "\033[36m"
_GREEN = "\033[32m"
_RED = "\033[31m"


def _strip_fake_source_lines(text: str) -> str:
    """Remove lines that look like doc citations when none was provided.

    Small models sometimes invent ``Source: foo.md`` even when explicitly
    forbidden.  Stripping these lines is a cheap guardrail for local demos.

    Args:
        text: Raw assistant reply text.

    Returns:
        Reply text with fake ``Source:`` lines removed.
    """
    kept: list[str] = []
    for line in text.split("\n"):
        stripped = line.strip()
        if stripped.lower().startswith("source:"):
            continue
        kept.append(line)
    return "\n".join(kept).strip()


_TICKET_ID = re.compile(r"TKT-[A-F0-9]{6}", re.I)

# Exact phrases (after lower + strip + optional trailing punctuation) where we
# skip RAG so ticket / email flows are not polluted by irrelevant chunks.
_CONVERSATIONAL_PHRASES = frozenset(
    {
        "yes",
        "yeah",
        "yep",
        "yup",
        "no",
        "nope",
        "nah",
        "ok",
        "okay",
        "sure",
        "please",
        "thanks",
        "thank you",
        "yes please",
        "no thanks",
        "go ahead",
        "sounds good",
        "alright",
        "fine",
        "k",
    }
)


def _is_conversational_turn(msg: str) -> bool:
    """Return True when RAG should be skipped for this user message.

    IMPORTANT: Do NOT use a loose word-count threshold — five-word questions
    like \"the mobile app keeps crashing\" must still run retrieval.
    """
    s = msg.strip()
    if not s:
        return True
    if "@" in s:
        return True
    if _TICKET_ID.search(s):
        return True

    low = s.lower().rstrip("!.?…").strip()
    if low in _CONVERSATIONAL_PHRASES:
        return True
    return False


def _width() -> int:
    """Return the current terminal width, defaulting to 80."""
    return shutil.get_terminal_size(fallback=(80, 24)).columns


def _hr(char: str = "─") -> str:
    """Return a horizontal rule scaled to the terminal width."""
    return _DIM + char * _width() + _RESET


def _print_banner(model: str, embed_model: str) -> None:
    """Print the startup banner showing both model names."""
    w = _width()
    title = "Sample App — Support Agent  (RAG)"
    subtitle = f"Chat: {model}  •  Embed: {embed_model}  •  Type 'quit' to exit"

    print()
    print(_hr("═"))
    print(_BOLD + _CYAN + title.center(w) + _RESET)
    print(_DIM + subtitle.center(w) + _RESET)
    print(_hr("═"))
    print()


def dispatch_tool(tool_name: str, tool_args: dict) -> str:
    """Call the appropriate tool handler and return its result as a JSON string.

    Args:
        tool_name: One of ``search_docs``, ``create_ticket``, ``get_ticket_status``.
        tool_args: Keyword arguments parsed from the model's tool-call payload.

    Returns:
        A JSON-encoded string of the tool's return value.
    """
    handler = TOOL_HANDLERS.get(tool_name)
    if handler is None:
        return json.dumps({"error": f"Unknown tool: {tool_name}"})

    safe_args = {
        k: (str(v) if isinstance(v, dict) else v) for k, v in tool_args.items()
    }
    result = handler(**safe_args)
    return json.dumps(result)


def run_agent_turn(
    history: list[dict],
    user_message: str,
    cfg: Config,
) -> tuple[str, list[dict]]:
    """Process a single user turn and return the assistant's reply plus updated history.

    Retrieval strategy: always run search_docs programmatically before the LLM
    call and inject the results as a system context message.  Small local models
    (llama3.2 3B) don't reliably call retrieval tools on their own — pre-fetching
    the context guarantees the LLM always answers from the docs rather than from
    its own (potentially hallucinated) knowledge.

    The LLM still has access to create_ticket and get_ticket_status as tools for
    when the user wants to take an action rather than just get an answer.

    Args:
        history: The conversation history so far (list of message dicts).
        user_message: The latest message from the user.
        cfg: Config instance controlling model and generation settings.

    Returns:
        A tuple of (assistant_reply_text, updated_history).
    """
    # Skip RAG only for emails, ticket IDs, and tiny acknowledgements — not for
    # short questions (e.g. five-word bug reports).
    _is_conv = _is_conversational_turn(user_message)
    retrieval = search_docs(user_message) if not _is_conv else {"found": False}
    if retrieval["found"]:
        sources = ", ".join(retrieval["sources"])
        user_content = (
            f"[Documentation from {sources}]\n"
            f"{retrieval['answer']}\n"
            f"[End of documentation]\n\n"
            f"Answer the following question using ONLY the documentation above. "
            f"Do not ask for a support ticket. Just answer.\n\n"
            f"Question: {user_message}"
        )
    elif not _is_conv:
        user_content = (
            "[No documentation match]\n"
            "The Sample App help docs do not contain a relevant article for this question.\n"
            "Hard rules for your reply:\n"
            "- Do NOT write the word 'Source' or any '.md' filename.\n"
            "- Do NOT list causes, fixes, or troubleshooting steps (you have no docs).\n"
            "- 2–3 sentences only: say the topic is not covered in the help center, "
            "then offer a support ticket. Ask for an email if you don't have one.\n\n"
            f"User question: {user_message}"
        )
    else:
        user_content = (
            "[Conversation continuation]\n"
            "- Do NOT invent help articles or write 'Source:' / any '.md' name.\n"
            "- If you offered a ticket and the user is agreeing, ask for their email "
            "if missing; do not demand crash logs first.\n"
            "- If you already have their email in this thread, call create_ticket.\n\n"
            f"User: {user_message}"
        )

    history = history + [{"role": "user", "content": user_content}]

    response = ollama.chat(
        model=cfg.model,
        messages=history,
        tools=_ACTION_TOOL_DEFINITIONS,
        options={"temperature": cfg.temperature, "num_predict": cfg.max_tokens},
    )

    msg = response.message
    tool_calls = msg.tool_calls or []

    assistant_entry: dict = {"role": "assistant", "content": msg.content or ""}
    if tool_calls:
        assistant_entry["tool_calls"] = [
            {"function": {"name": tc.function.name, "arguments": tc.function.arguments}}
            for tc in tool_calls
        ]
    history = history + [assistant_entry]

    for tc in tool_calls:
        tool_result = dispatch_tool(tc.function.name, tc.function.arguments)
        history = history + [{"role": "tool", "content": tool_result}]

    if tool_calls:
        follow_up = ollama.chat(
            model=cfg.model,
            messages=history,
            options={"temperature": cfg.temperature, "num_predict": cfg.max_tokens},
        )
        reply = follow_up.message.content or ""
        history = history + [{"role": "assistant", "content": reply}]
    else:
        reply = msg.content or ""

    if not retrieval["found"]:
        reply = _strip_fake_source_lines(reply)

    return reply, history


def build_initial_history(cfg: Config) -> list[dict]:
    """Return a fresh conversation history seeded with the system prompt.

    Args:
        cfg: Config instance whose ``system_prompt`` is used.

    Returns:
        A list containing a single system message dict.
    """
    return [{"role": "system", "content": cfg.system_prompt}]


def run_cli(cfg: Config | None = None) -> None:
    """Start the interactive terminal loop for the RAG support agent.

    Exits cleanly on ``quit``, ``exit``, or EOF.

    Args:
        cfg: Optional Config override — uses the module-level default when None.
    """
    cfg = cfg or default_config
    _print_banner(cfg.model, cfg.embed_model)

    # Build the RAG index at startup so the first query isn't slow.
    from tools import _get_index

    _get_index(cfg)

    history = build_initial_history(cfg)

    while True:
        try:
            user_input = input(_BOLD + _GREEN + "You  › " + _RESET).strip()
        except (EOFError, KeyboardInterrupt):
            print("\n" + _DIM + "Goodbye!" + _RESET)
            break

        if not user_input:
            continue

        if user_input.lower() in {"quit", "exit"}:
            print(_DIM + "Goodbye!" + _RESET)
            break

        print(_DIM + "  thinking…" + _RESET, end="\r")

        try:
            reply, history = run_agent_turn(history, user_input, cfg)
        except ollama.ResponseError as exc:
            print(_RED + f"  Error: {exc}" + _RESET + "\n")
            continue

        print(" " * _width(), end="\r")
        print(_BOLD + _CYAN + "Agent › " + _RESET + reply)
        print(_hr())


if __name__ == "__main__":
    run_cli()
