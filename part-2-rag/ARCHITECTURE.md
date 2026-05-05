# Architecture — Part 2 RAG Agent

This document covers what changed from Part 1, why it changed, and how the
RAG pipeline works end to end.

---

## What Changed from Part 1

| Component     | Part 1                              | Part 2                                      |
| ------------- | ----------------------------------- | ------------------------------------------- |
| Knowledge base| `faq.py` — 10 hardcoded dicts       | `docs/` — 7 markdown files, real prose      |
| Retrieval     | Keyword count matching              | Cosine similarity on embedding vectors      |
| Lookup tool   | `search_faq(query)`                 | `search_docs(query)`                        |
| New module    | —                                   | `rag.py` — chunking, embedding, index       |
| New model     | —                                   | `nomic-embed-text` (embedding model)        |
| Config        | `model`, `system_prompt`            | + `embed_model`, `docs_dir`, `chunk_size`, `top_k` |

The agent loop (`agent.py`) is identical. The two-pass pattern is identical.
Only the retrieval layer changed.

---

## The RAG Pipeline

### Phase 1 — Indexing (runs once at startup)

```
docs/*.md
    │
    ▼  chunk_text()
    │  Split each doc into 150-word chunks with 30-word overlap
    │
    ▼  embed_text()   [Ollama: nomic-embed-text]
    │  Each chunk → 768-dimensional float vector
    │
    ▼  list[Chunk]
       Held in memory for the lifetime of the process
```

### Phase 2 — Retrieval (runs on every query)

```
user query
    │
    ▼  embed_text()   [Ollama: nomic-embed-text]
    │  Query → 768-dimensional float vector
    │
    ▼  cosine_similarity() vs every chunk in the index
    │  Score = dot(query, chunk) / (|query| × |chunk|)
    │
    ▼  top_k=3 chunks sorted by score descending
    │
    ▼  Concatenated as context string → passed to LLM
```

---

## Why Cosine Similarity Works Here

Embeddings capture meaning, not exact words. Two sentences are similar in
embedding space if they mean similar things, regardless of the words used.

```
"the app looks completely empty"   →  embedding vector A
"dashboard isn't loading"          →  embedding vector B
"If your dashboard loads but shows nothing..."  →  embedding vector C

cosine(A, C) ≈ 0.82   ← high similarity, correct chunk retrieved
cosine(A, B) ≈ 0.74

Part 1 keyword match: "empty" not in keywords → score 0 → not found
Part 2 semantic search: meaning matches         → score 0.82 → found
```

---

## Why Chunking?

Embedding an entire document produces one vector that averages across all its
content. A document about billing will have billing-ish embeddings, but the
specific paragraph about invoice errors will be diluted.

Chunking splits documents into focused passages so each embedding represents
a specific topic. The retrieval then finds the right *paragraph*, not just the
right *document*.

**Chunk size (150 words) and overlap (30 words):**

- 150 words ≈ 1-2 paragraphs — enough context to be useful, focused enough
  to be specific.
- 30-word overlap means a sentence split at a boundary appears fully in at
  least one chunk. Without overlap, split sentences lose meaning.

---

## The Score Threshold and Ambiguity Guard

`search_docs` returns "not found" when the top cosine score is below **0.5**.

Additionally, if the best and second-best scores are within **0.035** of each
other *and* the top score is below **0.62**, the match is treated as ambiguous
and discarded. That avoids answering from the wrong page when two unrelated
topics score similarly (for example, a query about a **mobile app** falsely
matching a chunk that only mentions **mobile data** in a dashboard
network-troubleshooting list).

There is **no** `mobile.md` in the teaching corpus on purpose: questions like
*"the mobile app keeps crashing"* are **out of scope** for these docs. After
retrieval fails, the agent should offer a support ticket — not fabricate an
answer. That keeps Part 2 focused on **semantic retrieval when the knowledge
exists**, and on **honest limits** when it does not.

---

## Programmatic ``create_ticket`` after the user sends an email

Local 3B models often **say** a ticket was created without actually returning
``tool_calls``.  ``agent.py`` therefore detects a **plain email** on the
user’s turn when a recent assistant message asked for an **email** in the
context of a **ticket**, calls ``create_ticket`` in Python, injects the JSON
into the chat, and asks the model for a **single** confirmation reply **without**
tools so the ``ticket_id`` is real.

---

## Session meta-questions (no memory layer)

Phrases like *“what was my first question this session?”* are detected and
handled without RAG. The LLM call uses **only** the system prompt and that
message—**prior chat turns are omitted**—so the model cannot paraphrase the
transcript and fake recall. That makes the Part 2 limitation visible in the REPL;
**Part 3** adds genuine session or persistent memory.

---

## What This Architecture Does Not Handle

| Missing                  | Why it matters for Part 3+                                        |
| ------------------------ | ----------------------------------------------------------------- |
| No persistent index      | Re-embeds all docs on every startup (slow for large corpora)      |
| No re-ranking            | Top-k by cosine may not be the most relevant for the LLM          |
| No conversation context in retrieval | Query uses only the current message, not conversation history |
| No streaming             | Replies appear all at once                                        |
| No persistent memory     | Conversation resets on each run; Part 1’s in-memory `history` is not durable |

Part 3 in **this** repo is about **persistent / session memory** and managing
context. Improvements like **hybrid retrieval** (e.g. BM25 + dense vectors) are a
separate axis—better *document* matching—not a substitute for storage and
summaries; you can teach them in a later part if you extend the roadmap.
