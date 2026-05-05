"""Unit tests for the RAG pipeline in rag.py."""

from unittest.mock import patch

from rag import Chunk, chunk_text, cosine_similarity, load_docs, search_index

# ---------------------------------------------------------------------------
# chunk_text
# ---------------------------------------------------------------------------


class TestChunkText:
    def test_single_chunk_for_short_text(self):
        chunks = chunk_text("hello world", source="test.md", chunk_size=10, overlap=2)
        assert len(chunks) == 1
        assert chunks[0].text == "hello world"
        assert chunks[0].source == "test.md"

    def test_multiple_chunks_for_long_text(self):
        words = " ".join(str(i) for i in range(100))
        chunks = chunk_text(words, source="doc.md", chunk_size=20, overlap=5)
        assert len(chunks) > 1

    def test_overlap_means_words_repeated(self):
        words = " ".join(str(i) for i in range(30))
        chunks = chunk_text(words, source="doc.md", chunk_size=10, overlap=3)
        # Last 3 words of chunk 0 should appear at start of chunk 1
        tail = chunks[0].text.split()[-3:]
        head = chunks[1].text.split()[:3]
        assert tail == head

    def test_source_preserved_on_all_chunks(self):
        text = " ".join(["word"] * 200)
        chunks = chunk_text(text, source="billing.md", chunk_size=50, overlap=10)
        assert all(c.source == "billing.md" for c in chunks)

    def test_empty_text_returns_no_chunks(self):
        chunks = chunk_text("", source="empty.md")
        assert chunks == []

    def test_chunks_have_no_embeddings_by_default(self):
        chunks = chunk_text("some text here", source="doc.md")
        assert all(c.embedding == [] for c in chunks)


# ---------------------------------------------------------------------------
# cosine_similarity
# ---------------------------------------------------------------------------


class TestCosineSimilarity:
    def test_identical_vectors_return_one(self):
        v = [1.0, 2.0, 3.0]
        score = cosine_similarity(v, v)
        assert abs(score - 1.0) < 1e-6

    def test_orthogonal_vectors_return_zero(self):
        a = [1.0, 0.0]
        b = [0.0, 1.0]
        assert abs(cosine_similarity(a, b)) < 1e-6

    def test_opposite_vectors_return_minus_one(self):
        a = [1.0, 0.0]
        b = [-1.0, 0.0]
        assert abs(cosine_similarity(a, b) - (-1.0)) < 1e-6

    def test_zero_vector_returns_zero(self):
        assert cosine_similarity([0.0, 0.0], [1.0, 2.0]) == 0.0

    def test_similar_vectors_score_higher_than_dissimilar(self):
        base = [1.0, 1.0, 0.0]
        similar = [1.0, 0.9, 0.1]
        dissimilar = [0.0, 0.0, 1.0]
        assert cosine_similarity(base, similar) > cosine_similarity(base, dissimilar)


# ---------------------------------------------------------------------------
# load_docs
# ---------------------------------------------------------------------------


class TestLoadDocs:
    def test_loads_all_md_files(self, tmp_path):
        (tmp_path / "a.md").write_text("Content A")
        (tmp_path / "b.md").write_text("Content B")
        (tmp_path / "ignore.txt").write_text("Not markdown")

        docs = load_docs(str(tmp_path))
        filenames = [d[0] for d in docs]
        assert "a.md" in filenames
        assert "b.md" in filenames
        assert "ignore.txt" not in filenames

    def test_returns_sorted_order(self, tmp_path):
        (tmp_path / "z.md").write_text("Z")
        (tmp_path / "a.md").write_text("A")
        (tmp_path / "m.md").write_text("M")

        docs = load_docs(str(tmp_path))
        assert [d[0] for d in docs] == ["a.md", "m.md", "z.md"]

    def test_content_is_correct(self, tmp_path):
        (tmp_path / "test.md").write_text("Hello world")
        docs = load_docs(str(tmp_path))
        assert docs[0][1] == "Hello world"

    def test_empty_directory_returns_empty_list(self, tmp_path):
        assert load_docs(str(tmp_path)) == []


# ---------------------------------------------------------------------------
# search_index
# ---------------------------------------------------------------------------


class TestSearchIndex:
    def _make_index(self, texts: list[str]) -> list[Chunk]:
        """Build a minimal index with hand-crafted embeddings (no Ollama needed)."""
        chunks = []
        for i, text in enumerate(texts):
            # Embed as a one-hot-ish vector for predictable similarity.
            embedding = [0.0] * len(texts)
            embedding[i] = 1.0
            chunks.append(Chunk(text=text, source=f"doc{i}.md", embedding=embedding))
        return chunks

    def test_returns_top_k_results(self):
        index = self._make_index(["alpha", "beta", "gamma", "delta"])
        # Query embedding most similar to index[0]
        query_embedding = [1.0, 0.0, 0.0, 0.0]

        with patch("rag.embed_text", return_value=query_embedding):
            results = search_index("alpha query", index, "nomic-embed-text", top_k=2)

        assert len(results) == 2

    def test_results_sorted_by_score_descending(self):
        index = self._make_index(["alpha", "beta", "gamma"])
        query_embedding = [1.0, 0.0, 0.0]

        with patch("rag.embed_text", return_value=query_embedding):
            results = search_index("alpha query", index, "nomic-embed-text", top_k=3)

        scores = [r["score"] for r in results]
        assert scores == sorted(scores, reverse=True)

    def test_best_match_is_first(self):
        index = self._make_index(["alpha", "beta", "gamma"])
        query_embedding = [0.0, 1.0, 0.0]  # most similar to "beta"

        with patch("rag.embed_text", return_value=query_embedding):
            results = search_index("beta query", index, "nomic-embed-text", top_k=3)

        assert results[0]["text"] == "beta"

    def test_result_has_required_keys(self):
        index = self._make_index(["some text"])
        query_embedding = [1.0]

        with patch("rag.embed_text", return_value=query_embedding):
            results = search_index("query", index, "nomic-embed-text", top_k=1)

        assert {"text", "source", "score"} == set(results[0].keys())

    def test_empty_index_returns_empty_list(self):
        with patch("rag.embed_text", return_value=[1.0]):
            results = search_index("anything", [], "nomic-embed-text", top_k=3)
        assert results == []
