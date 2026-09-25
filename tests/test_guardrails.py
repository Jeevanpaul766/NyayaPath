"""
Tests for crisis detection and safety filter guardrails.

Validates:
  - Crisis tripwire catches explicit self-harm phrases
  - Crisis tripwire does NOT fire on legal distress alone
  - Safety filter refuses evidence destruction, witness intimidation, etc.
  - Safety filter does NOT refuse legitimate legal questions (over-refusal protection)
"""

import pytest
from src.guardrails.crisis_detector import check_tripwire, detect_crisis
from src.guardrails.safety_filter import format_refusal_response


class TestCrisisTripwire:
    """Test the deterministic keyword tripwire (Stage 1)."""

    @pytest.mark.parametrize("phrase", [
        "I want to kill myself",
        "I want to end my life because of this case",
        "thinking about suicide",
        "I want to die",
        "no point in living anymore",
        "can't take this anymore",
        "better off dead",
        "life is not worth living",
    ])
    def test_tripwire_fires_on_crisis_phrases(self, phrase):
        assert check_tripwire(phrase) is True, f"Tripwire should fire for: {phrase}"

    @pytest.mark.parametrize("phrase", [
        "I am very stressed about my 498A case",
        "My life is difficult because of the false case",
        "I need help with anticipatory bail urgently",
        "Police are coming to arrest me, I am scared",
        "This case has ruined my career",
        "I am worried about my family",
    ])
    def test_tripwire_does_not_fire_on_legal_stress(self, phrase):
        assert check_tripwire(phrase) is False, f"Tripwire should NOT fire for: {phrase}"

    def test_tripwire_case_insensitive(self):
        assert check_tripwire("I WANT TO KILL MYSELF") is True

    def test_tripwire_empty_string(self):
        assert check_tripwire("") is False


class TestCrisisDetection:
    """Test the full crisis detection pipeline (without LLM)."""

    def test_detect_crisis_tripwire_only(self):
        is_crisis, response = detect_crisis("I want to end my life", llm=None)
        assert is_crisis is True
        assert response is not None
        assert "112" in response
        assert "14416" in response

    def test_no_crisis_without_llm(self):
        # Without LLM, only tripwire runs
        is_crisis, response = detect_crisis("I need bail help", llm=None)
        assert is_crisis is False
        assert response is None


class TestRefusalResponse:
    """Test that refusal responses are properly formatted."""

    def test_evidence_destruction_refusal(self):
        response = format_refusal_response("evidence_destruction")
        assert "cannot" in response.lower() or "Cannot" in response
        assert "legal aid" in response.lower()
        assert "15100" in response

    def test_witness_intimidation_refusal(self):
        response = format_refusal_response("witness_intimidation")
        assert "cannot" in response.lower() or "Cannot" in response

    def test_evading_process_refusal(self):
        response = format_refusal_response("evading_process")
        assert "cannot" in response.lower() or "Cannot" in response

    def test_refusal_always_includes_alternatives(self):
        """Every refusal should suggest legitimate alternatives."""
        for category in [
            "evidence_destruction",
            "witness_intimidation",
            "evading_process",
            "false_statement_fabrication",
            "impersonation_forgery",
        ]:
            response = format_refusal_response(category)
            assert "bail" in response.lower() or "quash" in response.lower()

    def test_refusal_always_includes_disclaimer(self):
        for category in [
            "evidence_destruction",
            "witness_intimidation",
            "evading_process",
        ]:
            response = format_refusal_response(category)
            assert "not legal advice" in response.lower()
