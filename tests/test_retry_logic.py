"""
Tests for search reformulation, synthesis validation feedback, and retry routing.

Verifies:
  - build_reformulated_query targets official enactments and primary domains
  - search_public_sources_node uses reformulated query on retry
  - grade_and_retry_node extracts evidence and increments retry_count
  - synthesize_guidance prepends validation feedback when retrying
  - deterministic_output_check_node populates validation_feedback
  - route_after_grading and route_after_output_check terminate after MAX retries
"""

import pytest
from unittest.mock import patch, MagicMock

from src.retrieval.query_builder import build_search_query, build_reformulated_query
from src.synthesis.synthesizer import synthesize_guidance
from src.graph.nodes import (
    search_public_sources_node,
    grade_and_retry_node,
    deterministic_output_check_node,
)
from src.graph.edges import route_after_grading, route_after_output_check
from src.graph.builder import get_initial_state


class TestSearchReformulation:
    """Tests for query reformulation upon retry."""

    def test_reformulated_query_contains_official_site_and_acts(self):
        """Reformulated query must focus on primary bare acts and official domains."""
        query_bns = build_reformulated_query(
            original_query="theft procedure",
            issue_category="theft_property",
            code_regime="bns_bnss",
            retry_reason="insufficient_trusted_results",
        )
        assert "Bharatiya Nyaya Sanhita" in query_bns
        assert "indiacode.nic.in" in query_bns

        query_ipc = build_reformulated_query(
            original_query="cheating procedure",
            issue_category="cheating_fraud",
            code_regime="ipc_crpc",
            retry_reason="insufficient_trusted_results",
        )
        assert "Indian Penal Code" in query_ipc
        assert "indiacode.nic.in" in query_ipc

    def test_search_node_switches_to_reformulated_query_on_retry(self):
        """When retry_count > 0, search_public_sources_node uses reformulated query."""
        state = get_initial_state(user_story="Someone stole my car.")
        state["issue_category"] = "theft_property"
        state["code_regime"] = "bns_bnss"
        state["retry_count"] = 1  # Trigger retry logic

        with patch("src.graph.nodes.search_tavily", return_value=[]) as mock_search:
            updates = search_public_sources_node(state)

        assert "indiacode.nic.in" in updates["search_query"]
        assert "Bharatiya Nyaya Sanhita" in updates["search_query"]


class TestGradeAndEvidenceTracking:
    """Tests for grading, retry incrementation, and evidence extraction."""

    def test_grade_and_retry_increments_count_on_failure(self):
        """When results are unacceptable, retry_count is incremented."""
        state = get_initial_state(user_story="test")
        state["search_results"] = []  # Empty results fail grading
        state["retry_count"] = 0

        updates = grade_and_retry_node(state)
        assert updates["retry_count"] == 1
        assert "evidence" in updates

    def test_route_after_grading_allows_one_retry_then_terminates(self):
        """Edge routes to retry once, then proceeds to synthesize."""
        state = get_initial_state(user_story="test")
        state["search_results"] = []

        # Attempt 1 (retry_count == 1 <= MAX_SEARCH_RETRIES (1))
        state["retry_count"] = 1
        assert route_after_grading(state) == "search_public_sources"

        # Attempt 2 (retry_count == 2 > MAX_SEARCH_RETRIES (1))
        state["retry_count"] = 2
        assert route_after_grading(state) == "synthesize_guidance"


class TestSynthesisValidationFeedback:
    """Tests for feedback loop from sanitizer back to synthesizer."""

    def test_synthesizer_injects_corrective_feedback(self):
        """synthesize_guidance injects validation_feedback into LLM user prompt."""
        mock_llm = MagicMock()
        mock_response = MagicMock()
        mock_response.content = "Revised guidance content"
        mock_llm.invoke.return_value = mock_response

        feedback = [
            "Prohibited sections stripped due to regime mismatch (bns_bnss): IPC Section 498A.",
            "Missing disclaimer check phrase.",
        ]

        synthesize_guidance(
            user_story="My husband harassed me.",
            issue_category="matrimonial_cruelty",
            code_regime="bns_bnss",
            regime_explanation="Post-July 2024",
            search_results=[],
            llm=mock_llm,
            validation_feedback=feedback,
        )

        mock_llm.invoke.assert_called_once()
        invoked_messages = mock_llm.invoke.call_args[0][0]
        user_msg = invoked_messages[1].content

        assert "CORRECTION REQUIRED FROM PREVIOUS ATTEMPT" in user_msg
        assert "IPC Section 498A" in user_msg

    def test_output_check_populates_validation_feedback_on_violation(self):
        """deterministic_output_check_node captures violations in validation_feedback."""
        state = get_initial_state(user_story="test")
        state["code_regime"] = "bns_bnss"
        # Synthesized text contains prohibited IPC Section 420 for BNS regime
        state["raw_guidance"] = (
            "Under IPC Section 420, cheating is punishable.\n"
            "This is general educational information only and not legal advice. "
            "Every case is different. You must consult a qualified advocate before taking any step."
        )

        updates = deterministic_output_check_node(state)
        assert updates["output_check_passed"] is False
        assert len(updates["validation_feedback"]) > 0
        assert any("420" in fb for fb in updates["validation_feedback"])

    def test_route_after_output_check_retries_once_then_formats(self):
        """route_after_output_check retries up to MAX_OUTPUT_CHECK_RETRIES."""
        state = get_initial_state(user_story="test")
        state["output_check_passed"] = False

        # 1st failure (retries == 1 <= MAX_OUTPUT_CHECK_RETRIES)
        state["output_check_retries"] = 1
        assert route_after_output_check(state) == "synthesize_guidance"

        # 2nd failure (retries == 2 > MAX_OUTPUT_CHECK_RETRIES)
        state["output_check_retries"] = 2
        assert route_after_output_check(state) == "format_final_response"
