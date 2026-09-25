"""
Tests for pipeline telemetry, node execution tracing, and model configuration.

Verifies:
  - get_llm_model falls back to DEFAULT_MODEL or uses requested model
  - get_initial_state correctly initializes selected_model and node_trace
  - Nodes append telemetry entries with name, duration_ms, and completed flag
  - AgentState operator.add reducer accumulates traces across sequential nodes
"""

import pytest
from unittest.mock import patch, MagicMock

from src.config import get_llm_model, DEFAULT_MODEL, FALLBACK_MODEL
from src.graph.builder import get_initial_state, build_graph
from src.graph.nodes import (
    disclaimer_check_node,
    crisis_handler_node,
    refusal_handler_node,
    clarification_node,
)


class TestModelConfiguration:
    """Tests for get_llm_model helper."""

    def test_default_model_fallback(self):
        """None or empty string returns DEFAULT_MODEL."""
        assert get_llm_model(None) == DEFAULT_MODEL
        assert get_llm_model("") == DEFAULT_MODEL
        assert get_llm_model("   ") == DEFAULT_MODEL

    def test_custom_model_selection(self):
        """Custom valid model string is preserved."""
        assert get_llm_model(FALLBACK_MODEL) == FALLBACK_MODEL
        assert get_llm_model("llama3:8b") == "llama3:8b"


class TestNodeTelemetry:
    """Tests for execution timing and telemetry tracking in nodes."""

    def test_initial_state_has_telemetry_fields(self):
        """get_initial_state must initialize empty node_trace and store selected_model."""
        state = get_initial_state(
            user_story="test",
            selected_model=FALLBACK_MODEL,
        )
        assert state["selected_model"] == FALLBACK_MODEL
        assert state["node_trace"] == []

    def test_nodes_emit_timing_records(self):
        """Individual nodes must return a node_trace entry with duration_ms and completed."""
        state = get_initial_state(user_story="test")

        # Test disclaimer_check
        res1 = disclaimer_check_node(state)
        assert "node_trace" in res1
        assert len(res1["node_trace"]) == 1
        assert res1["node_trace"][0]["name"] == "disclaimer_check"
        assert res1["node_trace"][0]["duration_ms"] >= 0.0
        assert res1["node_trace"][0]["completed"] is True

        # Test crisis_handler
        res2 = crisis_handler_node(state)
        assert res2["node_trace"][0]["name"] == "crisis_handler"

        # Test refusal_handler
        res3 = refusal_handler_node(state)
        assert res3["node_trace"][0]["name"] == "refusal_handler"

        # Test clarification
        res4 = clarification_node(state)
        assert res4["node_trace"][0]["name"] == "clarification"

    def test_graph_accumulates_trace_steps(self):
        """Invoking the graph must accumulate trace steps across the execution path."""
        graph = build_graph()
        initial_state = get_initial_state(
            user_story="I am feeling suicidal and need help.",
            disclaimer_accepted=True,
        )

        with patch("src.guardrails.crisis_detector.detect_crisis", return_value=(True, "Helpline: 112")):
            result = graph.invoke(initial_state)

        trace = result.get("node_trace", [])
        assert len(trace) >= 2
        node_names = [t["name"] for t in trace]
        assert "disclaimer_check" in node_names
        assert "crisis_detection" in node_names
        assert "crisis_handler" in node_names
