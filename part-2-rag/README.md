# Part 2 — RAG Support Agent

The Part 1 agent answered from a hardcoded keyword list. This part replaces that
with a real RAG pipeline: markdown docs, chunking, embeddings, and cosine
similarity retrieval. Same agent loop. Completely different retrieval layer.

---

## What's inside

| File / Folder    | What it does                                                                 |
| ---------------- | ---------------------------------------------------------------------------- |
| `docs/`          | 7 markdown documentation files covering Sample App features                  |
| `rag.py`         | Chunking · embedding via Ollama · cosine similarity · index build + search   |
| `tools.py`       | `search_docs` (RAG) · `create_ticket` · `get_ticket_status`                  |
| `config.py`      | `Config` dataclass — chat model, embed model, chunk settings                 |
| `agent.py`       | Same two-pass loop as Part 1, updated tool name                              |
| `tests/`         | pytest tests for RAG functions, tools, and agent — all Ollama calls mocked   |

The doc set covers web dashboards, billing, reports, etc. It **deliberately**
does not cover native mobile apps or fully offline use — so you can demo
retrieval **misses** that correctly fall through to a ticket offer.

### Demo scripts (same story as the Part 2 blog post)

1. **Out of docs** — e.g. `mobile app crashes` → agent should say it’s not in the help center and offer a ticket (no invented fixes).
2. **Ticket flow** — `I need to report a bug` → `yes please` → `user@sample.com` → `what's the status of TKT-…` (paste the real id from the confirmation).
3. **Memory gap (Part 3 setup)** — after a few turns: `what was my first question this session?` That turn is sent to the model **without** earlier messages (only system + the meta prompt), so it cannot read the transcript—**real** session memory is Part 3. Quitting the CLI still wipes in-process history. *(This is different from Part 1’s “conversation state”: that’s just resending `history` in one run; it still isn’t durable memory.)*

---

## Setup

```bash
# 1. Start Ollama server
ollama serve

# 2. In a new terminal — pull both models
ollama pull llama3.2
ollama pull nomic-embed-text

# 3. Create virtual environment (or reuse the one from Part 1)
python3 -m venv .venv && source .venv/bin/activate

# 4. Install dependencies
pip install -r requirements.txt

# 5. Copy env file (optional — defaults work out of the box)
cp .env.example .env

# 6. Run
python agent.py
```

On first run you will see:

```
  Building RAG index… (this runs once at startup)
  Index ready — ~28 chunks from .../docs
```

The index is built by embedding every chunk in `docs/` using `nomic-embed-text`.
This takes ~10–20 seconds on first startup. Subsequent runs are the same speed
because Ollama caches the model in memory.

---

## The query that failed in Part 1 now works

```
You  › the app looks completely empty when I open it

Agent › This sounds like a dashboard display issue. Try hard-refreshing
        with Cmd+Shift+R, clearing your browser cache, or opening in
        incognito mode. Also check status.sampleapp.com for active
        incidents. (Source: dashboard.md)
```

In Part 1, "empty" and "looks" weren't keywords — the FAQ missed it. Here, the
embedding of "looks completely empty" is semantically close to the dashboard
troubleshooting content, so it retrieves the right chunk.

---

## Run tests

```bash
pytest tests/ -v
```

All Ollama calls are mocked — tests run without a live Ollama server.

---

## Lint and format

```bash
ruff check .
black --check .
```

---

## How it works

```
Startup:
  docs/*.md  →  chunk_text()  →  embed_text()  →  list[Chunk]  (index)

Per query:
  user query  →  embed_text()  →  cosine_similarity vs index  →  top_k chunks
              →  concat chunks as context  →  LLM  →  reply
```

See [ARCHITECTURE.md](ARCHITECTURE.md) for a full breakdown of what changed
from Part 1 and why.
