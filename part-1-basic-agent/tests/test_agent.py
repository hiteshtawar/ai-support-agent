"""Unit tests for conversation history management and tool dispatch in agent.py."""

import json
from types import SimpleNamespace
from unittest.mock import patch

from agent import build_initial_history, dispatch_tool, run_agent_turn
from config import Config

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_config() -> Config:
    return Config(model="llama3.2", temperature=0.0, max_tokens=256)


def _make_message(content: str, tool_calls: list | None = None) -> SimpleNamespace:
    """Build a minimal object that mimics an ollama Message (attribute access)."""
    return SimpleNamespace(content=content, tool_calls=tool_calls or [])


def _make_tool_call(name: str, arguments: dict) -> SimpleNamespace:
    """Build a minimal object that mimics an ollama ToolCall."""
    fn = SimpleNamespace(name=name, arguments=arguments)
    return SimpleNamespace(function=fn)


def _ollama_text_response(content: str) -> SimpleNamespace:
    """Minimal Ollama ChatResponse with only a text reply — no tool calls."""
    return SimpleNamespace(message=_make_message(content))


def _ollama_tool_response(tool_name: str, tool_args: dict) -> SimpleNamespace:
    """Minimal Ollama ChatResponse that requests a single tool call."""
    tc = _make_tool_call(tool_name, tool_args)
    return SimpleNamespace(message=_make_message("", tool_calls=[tc]))


# ---------------------------------------------------------------------------
# build_initial_history
# ---------------------------------------------------------------------------


class TestBuildInitialHistory:
    def test_returns_list_with_one_message(self):
        cfg = _make_config()
        history = build_initial_history(cfg)
        assert isinstance(history, list)
        assert len(history) == 1

    def test_first_message_is_system_role(self):
        cfg = _make_config()
        history = build_initial_history(cfg)
        assert history[0]["role"] == "system"

    def test_system_content_matches_config(self):
        cfg = _make_config()
        history = build_initial_history(cfg)
        assert history[0]["content"] == cfg.system_prompt

    def test_returns_new_list_each_call(self):
        cfg = _make_config()
        h1 = build_initial_history(cfg)
        h2 = build_initial_history(cfg)
        assert h1 is not h2


# ---------------------------------------------------------------------------
# dispatch_tool
# ---------------------------------------------------------------------------


class TestDispatchTool:
    def test_search_faq_dispatches_and_returns_json(self):
        result_str = dispatch_tool("search_faq", {"query": "how do I export"})
        result = json.loads(result_str)
        assert "found" in result

    def test_create_ticket_dispatches_and_returns_json(self):
        result_str = dispatch_tool(
            "create_ticket",
            {"issue": "Test issue", "user_email": "test@sample.com"},
        )
        result = json.loads(result_str)
        assert "ticket_id" in result

    def test_get_ticket_status_dispatches_and_returns_json(self):
        result_str = dispatch_tool("get_ticket_status", {"ticket_id": "TKT-DEMO99"})
        result = json.loads(result_str)
        assert "status" in result

    def test_unknown_tool_returns_error_json(self):
        result_str = dispatch_tool("nonexistent_tool", {})
        result = json.loads(result_str)
        assert "error" in result
        assert "nonexistent_tool" in result["error"]


# ---------------------------------------------------------------------------
# run_agent_turn — conversation history management
# ---------------------------------------------------------------------------


class TestRunAgentTurnHistory:
    def test_user_message_appended_to_history(self):
        cfg = _make_config()
        initial = build_initial_history(cfg)

        with patch("agent.ollama.chat", return_value=_ollama_text_response("Hello!")):
            _, new_history = run_agent_turn(initial, "Hi there", cfg)

        user_messages = [m for m in new_history if m["role"] == "user"]
        assert len(user_messages) == 1
        assert user_messages[0]["content"] == "Hi there"

    def test_assistant_reply_appended_to_history(self):
        cfg = _make_config()
        initial = build_initial_history(cfg)

        with patch(
            "agent.ollama.chat", return_value=_ollama_text_response("I can help!")
        ):
            _, new_history = run_agent_turn(initial, "Can you help?", cfg)

        assistant_messages = [m for m in new_history if m["role"] == "assistant"]
        assert len(assistant_messages) == 1

    def test_original_history_not_mutated(self):
        cfg = _make_config()
        initial = build_initial_history(cfg)
        original_length = len(initial)

        with patch("agent.ollama.chat", return_value=_ollama_text_response("Sure!")):
            run_agent_turn(initial, "Test mutation", cfg)

        assert len(initial) == original_length

    def test_multi_turn_accumulates_history(self):
        cfg = _make_config()
        history = build_initial_history(cfg)

        with patch("agent.ollama.chat", return_value=_ollama_text_response("Turn 1")):
            _, history = run_agent_turn(history, "Message 1", cfg)

        with patch("agent.ollama.chat", return_value=_ollama_text_response("Turn 2")):
            _, history = run_agent_turn(history, "Message 2", cfg)

        user_messages = [m for m in history if m["role"] == "user"]
        assert len(user_messages) == 2


# ---------------------------------------------------------------------------
# run_agent_turn — tool call dispatch path
# ---------------------------------------------------------------------------


class TestRunAgentTurnToolDispatch:
    def test_tool_result_appended_when_tool_called(self):
        cfg = _make_config()
        initial = build_initial_history(cfg)

        first_response = _ollama_tool_response("search_faq", {"query": "export"})
        second_response = _ollama_text_response("Here is what I found.")

        with patch("agent.ollama.chat", side_effect=[first_response, second_response]):
            _, history = run_agent_turn(initial, "How do I export?", cfg)

        tool_messages = [m for m in history if m["role"] == "tool"]
        assert len(tool_messages) == 1
        payload = json.loads(tool_messages[0]["content"])
        assert "found" in payload

    def test_final_reply_comes_from_second_inference(self):
        cfg = _make_config()
        initial = build_initial_history(cfg)

        first_response = _ollama_tool_response("search_faq", {"query": "dashboard"})
        second_response = _ollama_text_response("Your dashboard issue is covered here.")

        with patch("agent.ollama.chat", side_effect=[first_response, second_response]):
            reply, _ = run_agent_turn(initial, "Dashboard broken", cfg)

        assert reply == "Your dashboard issue is covered here."

    def test_no_tool_call_skips_second_inference(self):
        cfg = _make_config()
        initial = build_initial_history(cfg)

        with patch(
            "agent.ollama.chat", return_value=_ollama_text_response("Direct answer")
        ) as mock_chat:
            reply, _ = run_agent_turn(initial, "Hello", cfg)

        assert mock_chat.call_count == 1
        assert reply == "Direct answer"
