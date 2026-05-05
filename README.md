# Build a Production-Grade AI Support Agent from Scratch

A hands-on 5-part series where you build a production-grade AI support agent
from the ground up — adding RAG, embeddings, evals, and observability one layer
at a time. Local-first. No cloud required. No frameworks hiding the wires.

---

## The Series

| Part                                                        | What You Build                                                                       | Status        |
| ----------------------------------------------------------- | ------------------------------------------------------------------------------------ | ------------- |
| [Part 1 — Basic Agent](./part-1-basic-agent)                | Terminal agent · FAQ lookup · ticket creation · tool dispatch loop                   | ✅ Published  |
| Part 2 — RAG                                                | Replace keyword FAQ with a real docs corpus · chunk · embed · retrieve semantically  | 🔜 Coming soon |
| Part 3 — Memory                                             | Persistent conversation history · summarisation · context window management          | 🔜 Coming soon |
| Part 4 — Evals                                              | Test the agent's answers, not just the functions · eval harness · regression suite   | 🔜 Coming soon |
| Part 5 — Observability                                      | Traces · latency · token cost · production dashboards                                | 🔜 Coming soon |

---

## Why This Series

Most AI tutorials give you a demo that works once. This series builds a system
you can actually reason about:

- **No LangChain, no LlamaIndex** — every line of code is yours to read
- **Local-first** — Ollama + Llama 3.2, no cloud account, no API bills
- **Each part is a real improvement** — not a rewrite, just the next layer added
- **Tests at every stage** — pytest from Part 1, eval harness from Part 4

---

## Stack

| Tool                          | Purpose               |
| ----------------------------- | --------------------- |
| Python 3.11+                  | Everything            |
| [Ollama](https://ollama.com)  | Local LLM runner      |
| Llama 3.2                     | The model             |
| pytest                        | Unit tests            |
| black + ruff                  | Formatting and linting|

---

## Quick Start (Part 1)

```bash
# Start Ollama server
ollama serve

# In a new terminal
ollama pull llama3.2
git clone https://github.com/hiteshtawar/ai-support-agent
cd ai-support-agent/part-1-basic-agent
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python agent.py
```

Full setup and walkthrough → [part-1-basic-agent/README.md](./part-1-basic-agent/README.md)

---

## Blog

All parts are published on Hashnode with full explanations of the design
decisions, gotchas, and patterns behind the code.

→ [AI Native Engineering on Hashnode](https://hiteshtawar.hashnode.dev)

---

## Structure

```
ai-support-agent/
├── part-1-basic-agent/     # Terminal agent — FAQ, tools, loop
├── part-2-rag/             # Coming soon
├── part-3-memory/          # Coming soon
├── part-4-evals/           # Coming soon
└── part-5-observability/   # Coming soon
```
