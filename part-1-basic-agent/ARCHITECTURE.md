# Architecture — Part 1 Basic Agent

This document explains how the system works, where the "intelligence" lives, and
why each layer is built the way it is.

---

## System Layers

```
┌─────────────────────────────────────────────────────────────────┐
│                         User (terminal)                         │
└────────────────────────────┬────────────────────────────────────┘
                             │ plain text input
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    agent.py  —  the loop                        │
│                                                                 │
│  • Maintains conversation history (list of message dicts)       │
│  • Sends history + tool definitions to Ollama                   │
│  • Dispatches tool calls; re-sends results for a final reply    │
└────────────────────────────┬────────────────────────────────────┘
                             │ ollama.chat()
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│               Ollama / Llama 3.2  —  the LLM                    │  ← ML
│                                                                 │
│  • Understands intent from messy natural language               │
│  • Decides which tool to call (or whether to answer directly)   │
│  • Stitches tool results into a readable reply                  │
│  • Remembers the full conversation via the history list         │
└────────────────────────────┬────────────────────────────────────┘
                             │ structured tool calls
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│               tools.py  —  deterministic handlers               │  ← No ML
│                                                                 │
│  search_faq        keyword count matching against faq.py        │
│  create_ticket     uuid + timestamp, stored in a dict           │
│  get_ticket_status dict lookup with a deterministic fallback    │
└─────────────────────────────────────────────────────────────────┘
```

---

## Where the Intelligence Lives

There are two completely separate systems doing two different jobs.

### 1. The LLM (Ollama / Llama 3.2) — ML intelligence

Handles everything that requires understanding natural language:

| Job                            | Example                                                                           |
| ------------------------------ | --------------------------------------------------------------------------------- |
| **Intent mapping**             | "i see white screen" → calls `search_faq`, not `create_ticket`                   |
| **Vocabulary bridging**        | Connects "white screen" to the `dashboard` FAQ entry via `search_faq`            |
| **Conversation memory**        | Knows "what was my first question?" because the full history is in every request  |
| **Natural language generation**| Turns a raw JSON tool result into a friendly, readable reply                      |

The LLM cannot be replaced by a regex or a lookup table for these jobs.
It handles infinite variation in how users phrase things.

### 2. The tools (tools.py + faq.py) — deterministic code

Handles everything that requires precision and repeatability:

| Job                  | How it works                                                                                                        |
| -------------------- | ------------------------------------------------------------------------------------------------------------------- |
| **FAQ lookup**       | Counts how many of a FAQ entry's `keywords` appear in the lowercased query. Highest score wins. Pure Python, no ML.|
| **Ticket creation**  | `uuid.uuid4()` for the ID, `datetime.now()` for the timestamp. Stored in an in-memory dict.                        |
| **Ticket status**    | Dict lookup. Falls back to a deterministic demo status derived from the ticket ID string.                           |

These tools could run without an LLM at all — they're just functions.

---

## Why Split It This Way?

A traditional support system (regex + lookup table) handles the tools layer fine.
It breaks down at the LLM layer:

```
User types:  "white screen on my dash"

Regex system:  no match for "white screen on my dash" → fails
               (would need a rule for every phrasing variant)

This system:   LLM maps "white screen on my dash" → search_faq("white screen")
               search_faq finds "white screen" in keywords → returns answer
```

The LLM absorbs the infinite variation of human language.
The tools handle the precise, deterministic work the LLM shouldn't do
(generating IDs, querying data, maintaining state).

---

## Conversation History

Every request to Ollama includes the full conversation history:

```python
history = [
    {"role": "system",    "content": "<system prompt>"},
    {"role": "user",      "content": "i see white screen"},
    {"role": "assistant", "content": "", "tool_calls": [...]},
    {"role": "tool",      "content": "{\"found\": true, \"answer\": \"...\"}"},
    {"role": "assistant", "content": "Try clearing your cache..."},
    {"role": "user",      "content": "what was my first question?"},
]
```

The LLM has no memory of its own. "Memory" is just the history list being passed
on every call. This is the same pattern used by every chat LLM in production.

---

## What This Architecture Does Not Handle

This is Part 1 — intentionally minimal. Notable omissions:

| Missing               | Why it matters for Part 2+                                         |
| --------------------- | ------------------------------------------------------------------ |
| No real database      | Tickets vanish on restart                                          |
| No semantic search    | FAQ lookup misses paraphrases not in the keyword list              |
| No auth               | Anyone can create tickets as anyone                                |
| No streaming          | Replies appear all at once; slow on long answers                   |
| No retry logic        | One `ResponseError` ends the turn                                  |

Each of these is a natural expansion point for later parts of the series.
