"""Unit tests for the three tool handler functions in tools.py."""

import re

from tools import create_ticket, get_ticket_status, search_faq, _ticket_store

# ---------------------------------------------------------------------------
# search_faq
# ---------------------------------------------------------------------------


class TestSearchFaq:
    def test_known_keyword_returns_match(self):
        result = search_faq("my dashboard won't load")
        assert result["found"] is True
        assert "dashboard" in result["question"].lower()
        assert len(result["answer"]) > 0

    def test_export_keyword_returns_match(self):
        result = search_faq("how do I export a report")
        assert result["found"] is True
        assert "export" in result["question"].lower()

    def test_cancel_keyword_returns_match(self):
        result = search_faq("I want to cancel my plan")
        assert result["found"] is True
        assert "cancel" in result["question"].lower()

    def test_password_keyword_returns_match(self):
        result = search_faq("I forgot my password")
        assert result["found"] is True
        assert "password" in result["question"].lower()

    def test_unknown_query_returns_not_found(self):
        result = search_faq("tell me a joke about penguins")
        assert result["found"] is False
        assert result["question"] is None
        assert len(result["answer"]) > 0

    def test_empty_string_returns_not_found(self):
        result = search_faq("")
        assert result["found"] is False

    def test_whitespace_only_returns_not_found(self):
        result = search_faq("   ")
        assert result["found"] is False

    def test_partial_keyword_still_matches(self):
        # "invoice" should match the billing FAQ entry
        result = search_faq("where is my invoice")
        assert result["found"] is True

    def test_result_has_required_keys(self):
        result = search_faq("how do I invite a team member")
        assert {"found", "question", "answer"} == set(result.keys())


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

    def test_issue_and_email_are_stored(self):
        ticket = create_ticket("Wrong invoice amount", "billing@sample.com")
        assert ticket["issue"] == "Wrong invoice amount"
        assert ticket["user_email"] == "billing@sample.com"

    def test_ticket_stored_in_memory(self):
        ticket = create_ticket("Test storage", "store@sample.com")
        tid = ticket["ticket_id"]
        assert tid in _ticket_store

    def test_each_ticket_gets_unique_id(self):
        ids = {create_ticket("Issue", "a@sample.com")["ticket_id"] for _ in range(10)}
        assert len(ids) == 10

    def test_created_at_is_iso8601(self):
        from datetime import datetime

        ticket = create_ticket("Time check", "time@sample.com")
        # Should parse without raising
        dt = datetime.fromisoformat(ticket["created_at"])
        assert dt.tzinfo is not None  # must be timezone-aware


# ---------------------------------------------------------------------------
# get_ticket_status
# ---------------------------------------------------------------------------


class TestGetTicketStatus:
    def test_known_ticket_returns_open(self):
        ticket = create_ticket("Known ticket", "k@sample.com")
        tid = ticket["ticket_id"]
        status = get_ticket_status(tid)
        assert status["ticket_id"] == tid
        assert status["status"] == "open"
        assert tid in status["message"]

    def test_unknown_ticket_returns_demo_status(self):
        status = get_ticket_status("TKT-UNKNOWN")
        assert status["status"] in {
            "open",
            "in_progress",
            "waiting_on_customer",
            "resolved",
        }
        assert "not created in the current session" in status["message"]

    def test_normalizes_lowercase_id(self):
        ticket = create_ticket("Case check", "c@sample.com")
        tid_lower = ticket["ticket_id"].lower()
        status = get_ticket_status(tid_lower)
        assert status["ticket_id"] == ticket["ticket_id"]

    def test_result_has_required_keys(self):
        result = get_ticket_status("TKT-DEMO01")
        assert {"ticket_id", "status", "message"} == set(result.keys())

    def test_same_unknown_id_always_same_status(self):
        s1 = get_ticket_status("TKT-STABLE")
        s2 = get_ticket_status("TKT-STABLE")
        assert s1["status"] == s2["status"]
