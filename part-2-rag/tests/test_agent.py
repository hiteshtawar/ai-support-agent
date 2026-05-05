"""Unit tests for conversation history management and tool dispatch in agent.py."""

import json
from types import SimpleNamespace
from unittest.mock import patch

from agent import build_initial_history, dispatch_tool, run_agent_turn
from config import Config

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_NO_RETRIEVAL = {"found": False, "answer": "", "sources": []}
_WITH_RETRIEVAL = {
    "found": True,
    "answer": "Relevant doc content.",
    "sources": ["dashboard.md"],
}


def _make_config() -> Config:
    return Config(model="llama3.2", temperature=0.0, max_tokens=256)


def _make_message(content: str, tool_calls: list | None = None) -> SimpleNamespace:
    return SimpleNamespace(content=content, tool_calls=tool_calls or [])


def _make_tool_call(name: str, arguments: dict) -> SimpleNamespace:
    fn = SimpleNamespace(name=name, arguments=arguments)
    return SimpleNamespace(function=fn)


def _ollama_text_response(content: str) -> SimpleNamespace:
    return SimpleNamespace(message=_make_message(content))


def _ollama_tool_response(tool_name: str, tool_args: dict) -> SimpleNamespace:
    tc = _make_tool_call(tool_name, tool_args)
    return SimpleNamespace(message=_make_message("", tool_calls=[tc]))


# ---------------------------------------------------------------------------
# build_initial_history
# ---------------------------------------------------------------------------


class TestBuildInitialHistory:
    def test_returns_single_system_message(self):
        cfg = _make_config()
        history = build_initial_history(cfg)
        assert len(history) == 1
        assert history[0]["role"] == "system"

    def test_content_matches_config(self):
        cfg = _make_config()
        history = build_initial_history(cfg)
        assert history[0]["content"] == cfg.system_prompt

    def test_returns_new_list_each_call(self):
        cfg = _make_config()
        assert build_initial_history(cfg) is not build_initial_history(cfg)


# ---------------------------------------------------------------------------
# dispatch_tool
# ---------------------------------------------------------------------------


class TestDispatchTool:
    def test_unknown_tool_returns_error(self):
        result = json.loads(dispatch_tool("nonexistent", {}))
        assert "error" in result

    def test_create_ticket_dispatches(self):
        result = json.loads(
            dispatch_tool(
                "create_ticket", {"issue": "Test", "user_email": "t@sample.com"}
            )
        )
        assert "ticket_id" in result

    def test_get_ticket_status_dispatches(self):
        result = json.loads(
            dispatch_tool("get_ticket_status", {"ticket_id": "TKT-DEMO01"})
        )
        assert "status" in result

    def test_dict_arg_coerced_to_string(self):
        from unittest.mock import patch as _patch

        with _patch(
            "tools.search_index",
            return_value=[{"text": "x", "source": "s.md", "score": 0.9}],
        ):
            with _patch("tools._get_index", return_value=[]):
                result = json.loads(
                    dispatch_tool(
                        "search_docs",
                        {"query": {"type": "string", "description": "schema leak"}},
                    )
                )
        assert isinstance(result, dict)


# ---------------------------------------------------------------------------
# run_agent_turn — history management
# ---------------------------------------------------------------------------


class TestRunAgentTurnHistory:
    def test_user_message_appended(self):
        cfg = _make_config()
        history = build_initial_history(cfg)
        with patch("agent.search_docs", return_value=_NO_RETRIEVAL):
            with patch("agent.ollama.chat", return_value=_ollama_text_response("Hi!")):
                _, new_history = run_agent_turn(history, "Hello", cfg)
        user_msgs = [m for m in new_history if m["role"] == "user"]
        assert len(user_msgs) == 1
        assert user_msgs[0]["content"] == "Hello"

    def test_original_history_not_mutated(self):
        cfg = _make_config()
        initial = build_initial_history(cfg)
        original_len = len(initial)
        with patch("agent.search_docs", return_value=_NO_RETRIEVAL):
            with patch("agent.ollama.chat", return_value=_ollama_text_response("Hi!")):
                run_agent_turn(initial, "test", cfg)
        assert len(initial) == original_len

    def test_multi_turn_accumulates(self):
        cfg = _make_config()
        history = build_initial_history(cfg)
        with patch("agent.search_docs", return_value=_NO_RETRIEVAL):
            with patch("agent.ollama.chat", return_value=_ollama_text_response("1")):
                _, history = run_agent_turn(history, "msg1", cfg)
        with patch("agent.search_docs", return_value=_NO_RETRIEVAL):
            with patch("agent.ollama.chat", return_value=_ollama_text_response("2")):
                _, history = run_agent_turn(history, "msg2", cfg)
        assert len([m for m in history if m["role"] == "user"]) == 2

    def test_retrieved_context_embedded_in_user_message(self):
        cfg = _make_config()
        history = build_initial_history(cfg)
        with patch("agent.search_docs", return_value=_WITH_RETRIEVAL):
            with patch(
                "agent.ollama.chat", return_value=_ollama_text_response("Answer.")
            ):
                _, new_history = run_agent_turn(history, "dashboard broken", cfg)
        user_msgs = [m for m in new_history if m["role"] == "user"]
        assert len(user_msgs) == 1
        assert "dashboard.md" in user_msgs[0]["content"]
        assert "Relevant doc content." in user_msgs[0]["content"]

    def test_no_context_when_not_found_uses_plain_message(self):
        cfg = _make_config()
        history = build_initial_history(cfg)
        with patch("agent.search_docs", return_value=_NO_RETRIEVAL):
            with patch(
                "agent.ollama.chat", return_value=_ollama_text_response("Dunno.")
            ):
                _, new_history = run_agent_turn(history, "make coffee", cfg)
        user_msgs = [m for m in new_history if m["role"] == "user"]
        assert user_msgs[0]["content"] == "make coffee"


# ---------------------------------------------------------------------------
# run_agent_turn — tool dispatch path
# ---------------------------------------------------------------------------


class TestRunAgentTurnToolDispatch:
    def test_tool_result_appended(self):
        cfg = _make_config()
        initial = build_initial_history(cfg)
        first = _ollama_tool_response("get_ticket_status", {"ticket_id": "TKT-DEMO01"})
        second = _ollama_text_response("Your ticket is open.")

        with patch("agent.search_docs", return_value=_NO_RETRIEVAL):
            with patch("agent.ollama.chat", side_effect=[first, second]):
                _, history = run_agent_turn(initial, "check my ticket", cfg)

        tool_msgs = [m for m in history if m["role"] == "tool"]
        assert len(tool_msgs) == 1

    def test_final_reply_from_second_inference(self):
        cfg = _make_config()
        initial = build_initial_history(cfg)
        first = _ollama_tool_response("get_ticket_status", {"ticket_id": "TKT-DEMO01"})
        second = _ollama_text_response("Status is open.")

        with patch("agent.search_docs", return_value=_NO_RETRIEVAL):
            with patch("agent.ollama.chat", side_effect=[first, second]):
                reply, _ = run_agent_turn(initial, "check status", cfg)

        assert reply == "Status is open."

    def test_no_tool_skips_second_inference(self):
        cfg = _make_config()
        initial = build_initial_history(cfg)
        with patch("agent.search_docs", return_value=_NO_RETRIEVAL):
            with patch(
                "agent.ollama.chat", return_value=_ollama_text_response("Direct.")
            ) as mock:
                reply, _ = run_agent_turn(initial, "hello", cfg)
        assert mock.call_count == 1
        assert reply == "Direct."
