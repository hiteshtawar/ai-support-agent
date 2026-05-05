"""Unit tests for tool handler functions in tools.py."""

import re
from unittest.mock import patch

from tools import (
    _ticket_store,
    create_ticket,
    get_ticket_status,
    reset_index,
    search_docs,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_chunk(text: str, source: str = "test.md", score: float = 0.9) -> dict:
    """Minimal search result dict as returned by search_index."""
    return {"text": text, "source": source, "score": score}


# ---------------------------------------------------------------------------
# search_docs
# ---------------------------------------------------------------------------


class TestSearchDocs:
    def setup_method(self):
        reset_index()

    def test_found_result_returns_found_true(self):
        mock_results = [_make_chunk("Try clearing your cache.", score=0.85)]
        with patch("tools.search_index", return_value=mock_results):
            with patch("tools._get_index", return_value=[]):
                result = search_docs("dashboard won't load")
        assert result["found"] is True

    def test_found_result_contains_answer(self):
        mock_results = [_make_chunk("Clear your cache and cookies.", score=0.85)]
        with patch("tools.search_index", return_value=mock_results):
            with patch("tools._get_index", return_value=[]):
                result = search_docs("white screen")
        assert "Clear your cache" in result["answer"]

    def test_found_result_contains_sources(self):
        mock_results = [_make_chunk("Some info.", source="dashboard.md", score=0.85)]
        with patch("tools.search_index", return_value=mock_results):
            with patch("tools._get_index", return_value=[]):
                result = search_docs("dashboard issue")
        assert "dashboard.md" in result["sources"]

    def test_low_score_returns_not_found(self):
        mock_results = [_make_chunk("Irrelevant chunk.", score=0.2)]
        with patch("tools.search_index", return_value=mock_results):
            with patch("tools._get_index", return_value=[]):
                result = search_docs("how do I make coffee")
        assert result["found"] is False

    def test_empty_query_returns_not_found(self):
        with patch("tools._get_index", return_value=[]):
            result = search_docs("")
        assert result["found"] is False

    def test_whitespace_query_returns_not_found(self):
        with patch("tools._get_index", return_value=[]):
            result = search_docs("   ")
        assert result["found"] is False

    def test_dict_query_coerced_to_string(self):
        mock_results = [_make_chunk("Some answer.", score=0.85)]
        with patch("tools.search_index", return_value=mock_results):
            with patch("tools._get_index", return_value=[]):
                result = search_docs(
                    {"type": "string", "description": "The user's question"}
                )
        assert isinstance(result, dict)

    def test_ambiguous_close_scores_return_not_found(self):
        mock_results = [
            _make_chunk("Chunk A", source="a.md", score=0.55),
            _make_chunk("Chunk B", source="b.md", score=0.52),
        ]
        with patch("tools.search_index", return_value=mock_results):
            with patch("tools._get_index", return_value=[]):
                result = search_docs("vague unrelated query")
        assert result["found"] is False

    def test_clear_winner_passes_gap_check(self):
        mock_results = [
            _make_chunk("Winner", source="win.md", score=0.55),
            _make_chunk("Loser", source="lose.md", score=0.40),
        ]
        with patch("tools.search_index", return_value=mock_results):
            with patch("tools._get_index", return_value=[]):
                result = search_docs("something specific")
        assert result["found"] is True

    def test_empty_search_results_return_not_found(self):
        with patch("tools.search_index", return_value=[]):
            with patch("tools._get_index", return_value=[]):
                result = search_docs("anything")
        assert result["found"] is False

    def test_result_has_required_keys(self):
        mock_results = [_make_chunk("Answer text.", score=0.85)]
        with patch("tools.search_index", return_value=mock_results):
            with patch("tools._get_index", return_value=[]):
                result = search_docs("any question")
        assert {"found", "answer", "sources"} == set(result.keys())


# ---------------------------------------------------------------------------
# create_ticket
# ---------------------------------------------------------------------------


class TestCreateTicket:
    def test_returns_expected_keys(self):
        ticket = create_ticket("Dashboard not loading", "user@sample.com")
        assert {"ticket_id", "issue", "user_email", "status", "created_at"} <= set(
            ticket.keys()
        )

    def test_ticket_id_format(self):
        ticket = create_ticket("Login issue", "user@sample.com")
        assert re.match(r"^TKT-[A-F0-9]{6}$", ticket["ticket_id"])

    def test_initial_status_is_open(self):
        ticket = create_ticket("Export broken", "user@sample.com")
        assert ticket["status"] == "open"

    def test_each_ticket_gets_unique_id(self):
        ids = {create_ticket("Issue", "a@sample.com")["ticket_id"] for _ in range(10)}
        assert len(ids) == 10

    def test_ticket_stored_in_memory(self):
        ticket = create_ticket("Storage test", "store@sample.com")
        assert ticket["ticket_id"] in _ticket_store


# ---------------------------------------------------------------------------
# get_ticket_status
# ---------------------------------------------------------------------------


class TestGetTicketStatus:
    def test_known_ticket_returns_open(self):
        ticket = create_ticket("Known ticket", "k@sample.com")
        tid = ticket["ticket_id"]
        status = get_ticket_status(tid)
        assert status["status"] == "open"

    def test_unknown_ticket_returns_demo_status(self):
        status = get_ticket_status("TKT-UNKNOWN")
        assert status["status"] in {
            "open",
            "in_progress",
            "waiting_on_customer",
            "resolved",
        }

    def test_normalizes_lowercase_id(self):
        ticket = create_ticket("Case check", "c@sample.com")
        status = get_ticket_status(ticket["ticket_id"].lower())
        assert status["ticket_id"] == ticket["ticket_id"]

    def test_result_has_required_keys(self):
        result = get_ticket_status("TKT-DEMO01")
        assert {"ticket_id", "status", "message"} == set(result.keys())
