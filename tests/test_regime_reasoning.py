"""
Tests for the code regime classifier.

Validates:
  - Pre-cutoff dates resolve to ipc_crpc
  - Post-cutoff dates resolve to bns_bnss
  - Ambiguous / missing dates resolve to ambiguous
  - Date parsing handles multiple formats
  - Temporal hint extraction works
"""

import pytest
import datetime
from src.reasoning.regime_classifier import (
    parse_approximate_date,
    detect_temporal_hints,
    determine_regime,
    needs_date_clarification,
)
from src.config import CODE_TRANSITION_DATE


class TestDateParsing:
    """Test approximate date parsing from natural language."""

    def test_iso_date(self):
        result = parse_approximate_date("2024-03-15")
        assert result == datetime.date(2024, 3, 15)

    def test_month_year(self):
        result = parse_approximate_date("March 2024")
        assert result == datetime.date(2024, 3, 1)

    def test_month_year_abbreviated(self):
        result = parse_approximate_date("Jan 2023")
        assert result == datetime.date(2023, 1, 1)

    def test_bare_year(self):
        result = parse_approximate_date("2023")
        assert result == datetime.date(2023, 7, 1)  # Mid-year estimate

    def test_dmy_format(self):
        result = parse_approximate_date("15/03/2024")
        assert result == datetime.date(2024, 3, 15)

    def test_empty_returns_none(self):
        assert parse_approximate_date("") is None
        assert parse_approximate_date(None) is None

    def test_unparseable_returns_none(self):
        assert parse_approximate_date("sometime ago") is None


class TestTemporalHints:
    """Test relative time detection in user stories."""

    def test_recent_phrases(self):
        assert detect_temporal_hints("this happened last month") == "recent"
        assert detect_temporal_hints("a few weeks ago") == "recent"
        assert detect_temporal_hints("recently my wife filed") == "recent"

    def test_old_phrases(self):
        assert detect_temporal_hints("this happened years ago") == "old"
        assert detect_temporal_hints("back in 2022 we had a dispute") == "old"

    def test_neutral_returns_none(self):
        assert detect_temporal_hints("my wife filed a case") is None


class TestRegimeDetermination:
    """Test the core regime classification logic."""

    def test_clear_pre_cutoff(self):
        regime, explanation = determine_regime("January 2024", None)
        assert regime == "ipc_crpc"
        assert "IPC" in explanation or "Indian Penal Code" in explanation

    def test_clear_post_cutoff(self):
        regime, explanation = determine_regime("August 2024", None)
        assert regime == "bns_bnss"
        assert "BNS" in explanation or "Bharatiya" in explanation

    def test_exact_cutoff_date_is_new_code(self):
        regime, _ = determine_regime("July 2024", None)
        assert regime == "bns_bnss"

    def test_no_dates_returns_ambiguous(self):
        regime, _ = determine_regime(None, None, "my wife filed a case against me")
        assert regime == "ambiguous"

    def test_fir_date_with_recent_hint(self):
        regime, _ = determine_regime(
            None, "August 2024",
            user_story="this happened recently"
        )
        assert regime == "bns_bnss"

    def test_fir_pre_cutoff_without_recent_hint(self):
        regime, _ = determine_regime(
            None, "March 2024",
            user_story="my in-laws harassed me"
        )
        assert regime == "ipc_crpc"


class TestClarificationNeed:
    """Test whether the system correctly identifies when to ask for dates."""

    def test_needs_clarification_with_no_info(self):
        assert needs_date_clarification(None, None, "I have a legal problem") is True

    def test_no_clarification_with_offence_date(self):
        assert needs_date_clarification("March 2024", None) is False

    def test_no_clarification_with_fir_date(self):
        assert needs_date_clarification(None, "August 2024") is False

    def test_no_clarification_when_regime_determined(self):
        assert needs_date_clarification(
            None, None, "this happened last month recently"
        ) is False  # Temporal hint gives enough info


class TestNaturalPhrasingDateExtraction:
    """Test regime determination from natural language without explicit date fields.

    These tests verify the enhanced date extraction that doesn't require
    action-prefix keywords like 'incident' or 'offence' before the date.
    """

    def test_cheated_in_month_year(self):
        """CASE-03: 'cheated me in January 2024' should resolve to ipc_crpc."""
        regime, _ = determine_regime(
            None, None, "Someone cheated me of Rs 5 lakhs in January 2024"
        )
        assert regime == "ipc_crpc"

    def test_harassed_in_month_year(self):
        regime, _ = determine_regime(
            None, None, "My in-laws harassed me in August 2024"
        )
        assert regime == "bns_bnss"

    def test_attacked_with_month_year(self):
        regime, _ = determine_regime(
            None, None, "My neighbor attacked me in March 2024"
        )
        assert regime == "ipc_crpc"

    def test_stole_in_month_year(self):
        regime, _ = determine_regime(
            None, None, "Someone stole my phone in December 2024"
        )
        assert regime == "bns_bnss"

    def test_natural_sentence_with_date(self):
        """Date embedded in a natural sentence without action keyword."""
        regime, _ = determine_regime(
            None, None,
            "I lost my wallet with Rs 50000 in it and someone used my cards in February 2024"
        )
        assert regime == "ipc_crpc"

    def test_bare_year_in_natural_text(self):
        """A bare year mention should extract mid-year estimate."""
        regime, _ = determine_regime(
            None, None,
            "This dispute started in 2023 and has been ongoing"
        )
        assert regime == "ipc_crpc"  # 2023 mid-year is before cutoff

    def test_iso_date_in_narrative(self):
        """ISO date format in a narrative."""
        regime, _ = determine_regime(
            None, None,
            "The property dispute happened on 2024-08-15 and I need help"
        )
        assert regime == "bns_bnss"

    def test_dmy_date_in_narrative(self):
        """DD/MM/YYYY format in a narrative."""
        regime, _ = determine_regime(
            None, None,
            "The assault took place on 15/03/2024 at my workplace"
        )
        assert regime == "ipc_crpc"

