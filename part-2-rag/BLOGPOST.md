# From Keywords to Meaning: Adding RAG to Your AI Agent (Part 2 of 5)

> This is Part 2 of a 5-part series. Each part builds on the last. All code runs locally — no cloud account, no API bills.
> [← Part 1: Build the Basic Agent](https://hiteshtawar.hashnode.dev/build-a-production-grade-ai-support-agent-from-scratch-part-1-of-5)

---

In Part 1 we built a working support agent. It answers questions, creates tickets, remembers the conversation. It works.

Then we tried this:

```
You  › the app looks completely empty when I open it
```

Silence. No match. The agent offered to create a ticket.

The answer existed. The retrieval failed. `"empty"` wasn't a keyword. `"looks"` wasn't either.

That's not a code bug. That's the limit of keyword matching — and it's exactly what RAG is built to solve.

---

## What Changes in Part 2

One layer. Everything else stays the same.

| Component     | Part 1                        | Part 2                                    |
| ------------- | ----------------------------- | ----------------------------------------- |
| Knowledge base| `faq.py` — 10 hardcoded dicts | `docs/` — 7 markdown files, real prose    |
| Retrieval     | Keyword count matching        | Cosine similarity on embedding vectors    |
| Lookup        | `search_faq(query)`           | `search_docs(query)`                      |
| New module    | —                             | `rag.py` — chunk · embed · index · search |
| New model     | —                             | `nomic-embed-text` (embedding model)      |

The agent loop is identical. The two-pass pattern is identical. Only the retrieval layer changed — and that's the point. Good architecture means you can swap one layer without touching the others.

---

## Setup

```bash
# Start Ollama server
ollama serve

# In a new terminal — pull both models
ollama pull llama3.2
ollama pull nomic-embed-text

# Clone and go to Part 2
git clone https://github.com/hiteshtawar/ai-support-agent
cd ai-support-agent/part-2-rag

python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python agent.py
```

On first run:

```
  Building RAG index… (this runs once at startup)
  Index ready — 28 chunks from .../docs
```

---

## The Core Idea: Why Keywords Fail

Keyword matching counts exact string overlap. It cannot handle:

- Synonyms: `"empty"` vs `"blank"` vs `"nothing showing"`
- Paraphrases: `"looks completely empty"` vs `"dashboard not loading"`
- Context: `"I can't get in"` → login issue, not a physical door

RAG solves this with **embeddings** — numeric representations of meaning. Two sentences mean similar things → their embeddings are close in vector space → cosine similarity is high → correct chunk retrieved.

```
"the app looks completely empty"  →  [0.12, -0.45, 0.88, ...]  (768 numbers)
"dashboard loads but shows nothing"  →  [0.11, -0.43, 0.85, ...]

cosine similarity ≈ 0.91  ← semantically close, different words
```

---

## The Code

### `docs/` — Real Documentation

Seven markdown files replacing the hardcoded FAQ:

```
docs/
├── dashboard.md      # Loading issues, empty state, widgets
├── billing.md        # Plans, invoices, cancellation, upgrades
├── account.md        # Login, password reset, account deletion
├── reports.md        # Creating, exporting, scheduling reports
├── team.md           # Inviting members, roles, permissions
├── integrations.md   # Slack, Zapier, webhooks, API
└── notifications.md  # Email alerts, preferences, threshold alerts
```

Real prose. Not keyword lists. Part 3 will show why the format matters for chunking quality.

---

### `rag.py` — Four Functions

**`chunk_text`** — split a document into overlapping word windows:

```python
def chunk_text(text: str, source: str, chunk_size: int = 150, overlap: int = 30) -> list[Chunk]:
    words = text.split()
    step = chunk_size - overlap
    for i in range(0, len(words), step):
        chunk_words = words[i : i + chunk_size]
        chunks.append(Chunk(text=" ".join(chunk_words), source=source))
    return chunks
```

Why overlap? A sentence split at a chunk boundary loses meaning at both ends. 30-word overlap means every sentence appears fully in at least one chunk.

**`embed_text`** — one call to Ollama:

```python
def embed_text(text: str, model: str) -> list[float]:
    response = ollama.embeddings(model=model, prompt=text)
    return response["embedding"]
```

Returns 768 floats for `nomic-embed-text`. That's the meaning of the text, encoded as a point in 768-dimensional space.

**`cosine_similarity`** — pure Python, no numpy:

```python
def cosine_similarity(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    mag_a = math.sqrt(sum(x * x for x in a))
    mag_b = math.sqrt(sum(x * x for x in b))
    return dot / (mag_a * mag_b)
```

Score between -1.0 and 1.0. Higher = more similar. Two identical vectors = 1.0. Two completely unrelated vectors = near 0.

**`search_index`** — embed the query, score every chunk, return top-k:

```python
def search_index(query, index, embed_model, top_k=3):
    query_embedding = embed_text(query, embed_model)
    scored = [
        {"text": chunk.text, "source": chunk.source,
         "score": cosine_similarity(query_embedding, chunk.embedding)}
        for chunk in index
    ]
    scored.sort(key=lambda r: r["score"], reverse=True)
    return scored[:top_k]
```

This runs on every query. The index is built once at startup.

---

## The Two Phases

### Phase 1 — Indexing (startup, runs once)

```
docs/*.md  →  chunk_text()  →  embed_text()  →  list[Chunk]
```

Every chunk gets embedded and stored in memory. 28 chunks for our 7 docs. Takes ~10 seconds.

### Phase 2 — Retrieval (per query)

```
user query  →  embed_text()  →  cosine_similarity vs index  →  top 3 chunks
```

Takes ~200ms per query. The same embedding model is used for both phases — this matters. If you build the index with one model and query with another, the vectors are in different spaces and similarity scores are meaningless.

---

## A Design Decision Worth Knowing

### Pre-retrieval, not tool-calling

In Part 1, the LLM decided when to call `search_faq`. That worked for a chat model — but small local models (3B parameters) don't reliably call retrieval tools. They sometimes answer from their own knowledge instead.

Part 2 flips the control:

```
Old:  User → LLM → (maybe calls search_docs) → reply
New:  User → search_docs() always → inject context → LLM → reply
```

Retrieval is now infrastructure — it runs on every message before the LLM sees anything. The retrieved chunks are embedded directly in the user message:

```python
user_content = (
    f"[Documentation from {sources}]\n"
    f"{retrieval['answer']}\n"
    f"[End of documentation]\n\n"
    f"Answer the following question using ONLY the documentation above.\n\n"
    f"Question: {user_message}"
)
```

The LLM's only remaining tool calls are for actions: `create_ticket` and `get_ticket_status`. Retrieval is no longer a model decision.

This is how production RAG systems work. The retrieval step is deterministic infrastructure. The LLM synthesises — it doesn't retrieve.

---

## See It Work

```
You  › the app looks completely empty when I open it

Agent › Based on the documentation, if your dashboard is loading but
        showing nothing, this is usually a browser or cache issue.
        Try:
        1. Hard-refresh: Ctrl+Shift+R (Cmd+Shift+R on Mac)
        2. Clear your browser cache and cookies
        3. Open in an incognito window
        4. Check status.sampleapp.com for active incidents

        Source: dashboard.md
```

Same query. Part 1 returned nothing. Part 2 finds the answer.

---

## Run the Tests

```bash
pytest tests/ -v
```

All Ollama calls are mocked — tests run without a live server. The RAG tests use hand-crafted one-hot vectors to test similarity ranking without needing real embeddings.

---

## What's Next

The query `"the app looks completely empty"` now works. But try:

```
You  › what was my first question this session?
```

The agent has no idea. Every session starts fresh. The conversation history lives in a Python list that resets when the process ends.

That's the next problem. Part 3 adds persistent memory — conversation history that survives restarts, and context-window management so long sessions don't get slow and expensive.

→ Follow on Hashnode to get Part 3 when it drops
→ All code at [github.com/hiteshtawar/ai-support-agent](https://github.com/hiteshtawar/ai-support-agent)

---

*Hitesh Tawar is a Senior Software Engineer building AI-native systems. This series is for engineers who want to understand agentic AI from the ground up — local-first, no cloud required.*

`#ai` `#python` `#llm` `#rag` `#agentic-ai` `#tutorial`
