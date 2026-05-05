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

## What This Architecture Does Not Handle

| Missing                  | Why it matters for Part 3+                                        |
| ------------------------ | ----------------------------------------------------------------- |
| No persistent index      | Re-embeds all docs on every startup (slow for large corpora)      |
| No re-ranking            | Top-k by cosine may not be the most relevant for the LLM          |
| No conversation context in retrieval | Query uses only the current message, not conversation history |
| No streaming             | Replies appear all at once                                        |
| No persistent memory     | Conversation resets on each run                                   |

Persistent memory and context-aware retrieval are the focus of Part 3.
