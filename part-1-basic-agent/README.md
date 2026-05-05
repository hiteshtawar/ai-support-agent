# Part 1 — Basic Support Agent

A terminal-based AI support agent for **Sample App** by Sample Company.  
Users type questions; the agent answers from a hardcoded FAQ or offers to open a support ticket.

---

## What's inside

| File        | What it does                                                              |
| ----------- | ------------------------------------------------------------------------- |
| `faq.py`    | 10 hardcoded FAQ entries (billing, login, exports, dashboard, …)          |
| `tools.py`  | Three tool handlers: `search_faq`, `create_ticket`, `get_ticket_status`   |
| `config.py` | `Config` dataclass — model name, temperature, system prompt               |
| `agent.py`  | Agent loop: reads input → calls Ollama → dispatches tools → prints reply  |
| `tests/`    | pytest unit tests for tools and agent logic                               |

---

## Setup

```bash
# 1. Start the Ollama server (keep this terminal open, or use brew services)
ollama serve

# Alternative — run Ollama as a background service that survives reboots:
# brew services start ollama

# 2. In a new terminal — pull the model
ollama pull llama3.2

# 3. Create a virtual environment
python3 -m venv .venv && source .venv/bin/activate

# 4. Install dependencies
pip install -r requirements.txt

# 5. Copy the env file (optional — defaults work out of the box)
cp .env.example .env

# 6. Run the agent
python agent.py
```

---

## Expected conversation

```
══════════════════════════════════════════════════════════
              Sample App — Support Agent
            Model: llama3.2  •  Type 'quit' to exit
══════════════════════════════════════════════════════════

You  › my dashboard won't load
Agent › Try these steps:
        1. Hard-refresh with Ctrl+Shift+R.
        2. Clear your browser cache.
        3. Check status.sampleapp.com for active incidents.
        If the issue persists, I can open a support ticket for you.
──────────────────────────────────────────────────────────
You  › please open a ticket
Agent › Sure — what's your email address?
──────────────────────────────────────────────────────────
You  › user@sample.com
Agent › Done! Your ticket ID is TKT-4F2A1C.
        Our team will follow up at user@sample.com.
──────────────────────────────────────────────────────────
You  › quit
Goodbye!
```

---

## Run tests

```bash
pytest tests/ -v
```

---

## Lint and format

```bash
ruff check .
black --check .

# Auto-fix
black .
ruff check . --fix
```

---

## How it works (30-second version)

1. **User types** a message into the terminal.
2. **`agent.py`** appends the message to the conversation history and sends the whole history to Ollama with the three tool definitions.
3. **Ollama/Llama 3.2** decides whether to answer directly or call a tool.
4. If a tool is requested, **`agent.py`** dispatches to the matching handler in `tools.py` and appends the result to history.
5. A second Ollama call turns the raw tool result into a natural-language reply.
6. The reply is printed and the loop repeats.

No frameworks. No databases. Every line is plain Python.

For a deeper explanation of what the LLM does vs. what the tools do, and why
the system is split this way, see [ARCHITECTURE.md](ARCHITECTURE.md).
