"""Main agent loop for the Sample Company terminal support agent."""

import json
import shutil

import ollama

from config import Config, config as default_config
from tools import TOOL_DEFINITIONS, TOOL_HANDLERS

# ANSI colour codes — no dependencies, works on macOS/Linux terminals.
_RESET = "\033[0m"
_BOLD = "\033[1m"
_DIM = "\033[2m"
_CYAN = "\033[36m"
_GREEN = "\033[32m"
_YELLOW = "\033[33m"
_RED = "\033[31m"
_BG_DARK = "\033[48;5;235m"


def _width() -> int:
    """Return the current terminal width, defaulting to 80."""
    return shutil.get_terminal_size(fallback=(80, 24)).columns


def _hr(char: str = "─") -> str:
    """Return a horizontal rule scaled to the terminal width."""
    return _DIM + char * _width() + _RESET


def _print_banner(model: str) -> None:
    """Print the startup banner with product name, model, and help hint."""
    w = _width()
    title = "Sample App — Support Agent"
    subtitle = f"Model: {model}  •  Type 'quit' to exit"

    print()
    print(_hr("═"))
    print(_BOLD + _CYAN + title.center(w) + _RESET)
    print(_DIM + subtitle.center(w) + _RESET)
    print(_hr("═"))
    print()


def dispatch_tool(tool_name: str, tool_args: dict) -> str:
    """Call the appropriate tool handler and return its result as a JSON string.

    Args:
        tool_name: One of ``search_faq``, ``create_ticket``, ``get_ticket_status``.
        tool_args: Keyword arguments parsed from the model's tool-call payload.

    Returns:
        A JSON-encoded string of the tool's return value, ready to be added to
        the conversation history as a ``tool`` role message.
    """
    handler = TOOL_HANDLERS.get(tool_name)
    if handler is None:
        return json.dumps({"error": f"Unknown tool: {tool_name}"})

    # Small local models (e.g. llama3.2 3B) sometimes pass the parameter schema
    # dict as the argument value instead of the actual string.  Coerce any dict
    # value that looks like a schema spec back to a plain string so the handlers
    # don't crash.
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

    The function implements a simple agentic loop:
    1. Append the user message to history.
    2. Send the full history to Ollama with tool definitions.
    3. If the model requests tool calls, dispatch each one, append the results,
       then send history back to the model to get a final natural-language reply.
    4. Append the final assistant reply and return it.

    Args:
        history: The conversation history so far (list of message dicts).
        user_message: The latest message from the user.
        cfg: Config instance controlling model and generation settings.

    Returns:
        A tuple of (assistant_reply_text, updated_history).
    """
    history = history + [{"role": "user", "content": user_message}]

    response = ollama.chat(
        model=cfg.model,
        messages=history,
        tools=TOOL_DEFINITIONS,
        options={"temperature": cfg.temperature, "num_predict": cfg.max_tokens},
    )

    # response.message is an ollama Message object — use attribute access, not
    # dict access, so tool_calls is never silently swallowed as None.
    msg = response.message
    tool_calls = msg.tool_calls or []

    # Serialize to a plain dict before appending so history stays JSON-safe.
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

    # If the model made tool calls we need a second inference pass to turn the
    # raw tool results into a natural-language reply.
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
    """Start the interactive terminal loop for the support agent.

    Reads user input from stdin, runs each turn through the agent, and prints
    the assistant's reply.  Exits cleanly on ``quit``, ``exit``, or EOF.

    Args:
        cfg: Optional Config override — uses the module-level default when None.
    """
    cfg = cfg or default_config
    history = build_initial_history(cfg)

    _print_banner(cfg.model)

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

        print(" " * _width(), end="\r")  # clear the "thinking…" line
        print(_BOLD + _CYAN + "Agent › " + _RESET + reply)
        print(_hr())


if __name__ == "__main__":
    run_cli()
