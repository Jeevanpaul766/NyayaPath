"""
Tests for multi-turn conversation memory and clarification state preservation.

Verifies:
  - First turn populates original_user_story if not previously set.
  - Follow-up turns preserve original_user_story context for classification.
  - Follow-up date responses resolve needs_clarification and update regime.
  - get_initial_state preserves original_user_story and prior conversation messages.
"""

import pytest
from unittest.mock import patch, MagicMock
from langchain_core.messages import HumanMessage, AIMessage

from src.graph.builder import get_initial_state
from src.graph.nodes import classify_and_clarify_node


class TestMultiTurnContextPreservation:
    """Tests for multi-turn conversation memory and clarification."""

    def test_first_turn_sets_original_user_story(self):
        """First turn without original_user_story should set it to user_story."""
        state = get_initial_state(user_story="Someone stole my bicycle.")
        state["original_user_story"] = ""

        with patch("src.graph.nodes.classify_issue", return_value="Theft / Property Offence"), \
             patch("src.graph.nodes._get_llm"):
            updates = classify_and_clarify_node(state)

        assert updates.get("original_user_story") == "Someone stole my bicycle."

    def test_follow_up_date_merges_with_original_story_bns(self):
        """When follow-up is just a date after July 2024, context is preserved and regime resolved to BNS."""
        original_story = "My employer refused to pay my wages for 3 months and assaulted me."
        follow_up_input = "The assault happened on 15 August 2024."

        state = get_initial_state(
            user_story=follow_up_input,
            original_user_story=original_story,
        )

        with patch("src.graph.nodes.classify_issue", return_value="Assault / Criminal Violence") as mock_classify, \
             patch("src.graph.nodes._get_llm"):
            updates = classify_and_clarify_node(state)

        # Classification must have been run against the original scenario context, not just the date
        mock_classify.assert_called_once()
        called_story = mock_classify.call_args[0][0]
        assert "employer refused to pay" in called_story

        # Regime should be resolved to bns_bnss
        assert updates["code_regime"] == "bns_bnss"
        assert updates["needs_clarification"] is False

    def test_follow_up_date_merges_with_original_story_ipc(self):
        """When follow-up is a date before July 2024, regime resolves to IPC."""
        original_story = "A shopkeeper cheated me with counterfeit electronic goods."
        follow_up_input = "This took place in January 2024."

        state = get_initial_state(
            user_story=follow_up_input,
            original_user_story=original_story,
        )

        with patch("src.graph.nodes.classify_issue", return_value="Cheating / Fraud") as mock_classify, \
             patch("src.graph.nodes._get_llm"):
            updates = classify_and_clarify_node(state)

        assert updates["code_regime"] == "ipc_crpc"
        assert updates["needs_clarification"] is False

    def test_initial_state_preserves_messages_and_original_story(self):
        """get_initial_state stores prior messages and preserves original_user_story."""
        prior_messages = [
            HumanMessage(content="My gold chain was snatched."),
            AIMessage(content="When did this incident occur?"),
        ]
        state = get_initial_state(
            user_story="It happened yesterday, September 2024.",
            original_user_story="My gold chain was snatched.",
            messages=prior_messages,
        )

        assert len(state["messages"]) == 2
        assert state["original_user_story"] == "My gold chain was snatched."
        assert state["user_story"] == "It happened yesterday, September 2024."
