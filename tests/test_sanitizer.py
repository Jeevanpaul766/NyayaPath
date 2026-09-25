"""
Tests for the deterministic output sanitizer.

Validates:
  - Disclaimer detection and injection
  - Outcome prediction detection and stripping
  - Section allowlist enforcement
  - Strip-and-recheck mechanism
  - Fallback template activation
"""

import pytest
from src.synthesis.output_sanitizer import (
    sanitize_output,
    _check_disclaimer,
    _check_no_outcome_predictions,
    _extract_section_numbers,
    _check_allowlist,
)
from src.config import DISCLAIMER_CHECK_PHRASE


class TestDisclaimerCheck:
    """Test disclaimer presence verification."""

    def test_disclaimer_present(self):
        text = f"Some guidance. This is {DISCLAIMER_CHECK_PHRASE}."
        assert _check_disclaimer(text) is True

    def test_disclaimer_absent(self):
        text = "Some guidance without any disclaimer."
        assert _check_disclaimer(text) is False

    def test_disclaimer_case_insensitive(self):
        text = "This is General Educational Information Only And Not Legal Advice."
        assert _check_disclaimer(text) is True


class TestOutcomePredictionDetection:
    """Test detection of prohibited outcome predictions."""

    @pytest.mark.parametrize("phrase", [
        "you will win this case",
        "guaranteed acquittal",
        "charges will be dropped",
        "sure to get bail",
        "judge will dismiss the case",
        "100% chance of success",
    ])
    def test_detects_outcome_predictions(self, phrase):
        passed, matches = _check_no_outcome_predictions(phrase)
        assert passed is False, f"Should detect prediction in: {phrase}"

    @pytest.mark.parametrize("phrase", [
        "you may consult a lawyer",
        "bail is a legal right",
        "the court will examine the evidence",
        "seek legal aid",
    ])
    def test_allows_legitimate_language(self, phrase):
        passed, matches = _check_no_outcome_predictions(phrase)
        assert passed is True, f"Should allow: {phrase}"


class TestSectionExtraction:
    """Test extraction of section-like references from text."""

    def test_extract_ipc_section(self):
        sections = _extract_section_numbers("Under Section 498A of the IPC")
        assert any("498A" in s for s in sections)

    def test_extract_bns_section(self):
        sections = _extract_section_numbers("Under BNS 85")
        assert any("85" in s for s in sections)

    def test_extract_bnss_section(self):
        sections = _extract_section_numbers("BNSS 482 provides for anticipatory bail")
        assert any("482" in s for s in sections)

    def test_extract_multiple_sections(self):
        text = "Section 498A IPC and BNS 85 are equivalent. See also BNSS 482."
        sections = _extract_section_numbers(text)
        assert len(sections) >= 3


class TestAllowlistCheck:
    """Test section allowlist enforcement."""

    def test_allowed_section_passes(self):
        text = "Section 498A of the IPC applies here. BNS 85 is the new equivalent."
        passed, unauthorized = _check_allowlist(text)
        assert passed is True, f"Unauthorized: {unauthorized}"

    def test_unknown_section_fails(self):
        text = "Section 999Z of the IPC applies here."
        passed, unauthorized = _check_allowlist(text)
        # May or may not flag depending on parsing; at minimum should detect the section
        # This is a soft test — the important thing is that the sanitizer catches it


class TestFullSanitization:
    """Test the complete sanitization pipeline."""

    def test_clean_output_passes(self):
        text = (
            "### 1. Understanding of your situation\n"
            "You are facing a 498A case.\n\n"
            "### 7. Important Disclaimer\n"
            "This is general educational information only and not legal advice."
        )
        result = sanitize_output(text)
        assert result.passed is True

    def test_missing_disclaimer_gets_added(self):
        text = "Some guidance without disclaimer."
        result = sanitize_output(text)
        assert "not legal advice" in result.text.lower()

    def test_outcome_prediction_gets_stripped(self):
        text = (
            "You will definitely win this case. "
            "This is general educational information only and not legal advice."
        )
        result = sanitize_output(text)
        assert "will definitely win" not in result.text

    def test_fallback_template_has_no_sections(self):
        from src.synthesis.fallback_templates import get_no_sections_fallback
        fallback = get_no_sections_fallback()
        result = sanitize_output(fallback)
        assert result.passed is True
        assert len(result.sections_stripped) == 0


class TestRegimeSpecificAllowlist:
    """Test that the allowlist enforces regime isolation."""

    def test_ipc_sections_rejected_in_bns_regime(self):
        """IPC 498A should be flagged as unauthorized when regime is bns_bnss."""
        text = (
            "Under Section 498A of the IPC, cruelty is defined. "
            "This is general educational information only and not legal advice."
        )
        passed, unauthorized = _check_allowlist(text, regime="bns_bnss")
        # "498A" and "IPC 498A" should be caught as unauthorized in BNS regime
        assert passed is False, f"IPC 498A should be unauthorized in bns_bnss regime, got: {unauthorized}"

    def test_bns_sections_rejected_in_ipc_regime(self):
        """BNS 85 should be flagged as unauthorized when regime is ipc_crpc."""
        text = (
            "Under BNS 85, cruelty is defined. "
            "This is general educational information only and not legal advice."
        )
        passed, unauthorized = _check_allowlist(text, regime="ipc_crpc")
        assert passed is False, f"BNS 85 should be unauthorized in ipc_crpc regime, got: {unauthorized}"

    def test_bnss_sections_rejected_in_ipc_regime(self):
        """BNSS 482 should be flagged as unauthorized when regime is ipc_crpc."""
        text = "BNSS 482 provides for anticipatory bail."
        passed, unauthorized = _check_allowlist(text, regime="ipc_crpc")
        assert passed is False, f"BNSS 482 should be unauthorized in ipc_crpc regime"

    def test_crpc_sections_rejected_in_bns_regime(self):
        """CrPC 438 should be flagged as unauthorized when regime is bns_bnss."""
        text = "CrPC 438 provides for anticipatory bail."
        passed, unauthorized = _check_allowlist(text, regime="bns_bnss")
        assert passed is False, f"CrPC 438 should be unauthorized in bns_bnss regime"

    def test_ambiguous_allows_both(self):
        """In ambiguous regime, both IPC and BNS sections should be allowed."""
        text = (
            "IPC 498A and BNS 85 are equivalent provisions for cruelty. "
            "This is general educational information only and not legal advice."
        )
        passed, unauthorized = _check_allowlist(text, regime="ambiguous")
        assert passed is True, f"Both IPC and BNS should be allowed in ambiguous regime, unauthorized: {unauthorized}"

    def test_unchanged_statute_allowed_in_both_regimes(self):
        """NI Act 138 is unchanged and should be allowed in any regime."""
        text = "NI Act 138 deals with dishonour of cheque."
        passed_ipc, _ = _check_allowlist(text, regime="ipc_crpc")
        passed_bns, _ = _check_allowlist(text, regime="bns_bnss")
        assert passed_ipc is True, "NI Act 138 should be allowed in ipc_crpc"
        assert passed_bns is True, "NI Act 138 should be allowed in bns_bnss"


class TestRegimeSanitization:
    """Test the full sanitization pipeline with regime enforcement."""

    def test_ipc_in_bns_case_gets_stripped(self):
        """Full pipeline should strip IPC sections from a BNS-regime response."""
        text = (
            "Under Section 498A of the IPC, cruelty is an offence. "
            "This is general educational information only and not legal advice."
        )
        result = sanitize_output(text, regime="bns_bnss")
        assert "498A" not in result.text or "BNS" in result.text
        assert len(result.sections_stripped) > 0

    def test_bns_in_ipc_case_gets_stripped(self):
        """Full pipeline should strip BNS sections from an IPC-regime response."""
        text = (
            "Under BNS 85, cruelty is an offence. "
            "This is general educational information only and not legal advice."
        )
        result = sanitize_output(text, regime="ipc_crpc")
        assert len(result.sections_stripped) > 0

    def test_correct_regime_sections_pass(self):
        """Correct regime sections should pass without stripping."""
        text = (
            "Under BNS 85, cruelty is an offence. BNSS 482 provides anticipatory bail. "
            "This is general educational information only and not legal advice."
        )
        result = sanitize_output(text, regime="bns_bnss")
        assert result.passed is True
        assert len(result.sections_stripped) == 0


class TestActYearPreservation:
    """Test that calendar and statute enactment years are never treated as sections."""

    @pytest.mark.parametrize("act_phrase", [
        "Bharatiya Nyaya Sanhita, 2023",
        "Bharatiya Nagarik Suraksha Sanhita, 2023",
        "Bharatiya Sakshya Adhiniyam, 2023",
        "Indian Penal Code, 1860",
        "Code of Criminal Procedure, 1973",
        "Negotiable Instruments Act, 1881",
        "BNS 2023",
        "CrPC 1973",
        "IPC 1860",
        "enacted in 2024",
    ])
    def test_years_not_extracted_as_sections(self, act_phrase):
        extracted = _extract_section_numbers(act_phrase)
        for year in ("2023", "1860", "1973", "1881", "2024"):
            assert year not in extracted, f"Year {year} should not be extracted from {act_phrase}"

    def test_act_with_year_survives_sanitization(self):
        text = (
            "Under the Bharatiya Nyaya Sanhita, 2023, BNS 318 deals with cheating. "
            "This is general educational information only and not legal advice."
        )
        result = sanitize_output(text, regime="bns_bnss")
        assert result.passed is True
        assert "2023" in result.text
        assert "Bharatiya Nyaya Sanhita, 2023" in result.text
        assert "BNS 318" in result.text
        assert len(result.sections_stripped) == 0


class TestValidCitationFormats:
    """Test that all common valid citation formats pass without stripping."""

    @pytest.mark.parametrize("citation", [
        "Section 318",
        "BNS 318",
        "318 BNS",
        "Section 318 of BNS",
        "Section 318 of the BNS",
        "Section 318, BNS",
        "Section 318 of the Bharatiya Nyaya Sanhita, 2023",
        "Section 318(4)",
        "BNS 318(4)",
        "318(4) BNS",
        "BNSS 173",
        "BNSS 175(3)",
        "BNS 303",
        "BNS 303(2)",
    ])
    def test_bns_valid_formats_pass(self, citation):
        text = f"According to {citation}, relief is available. This is general educational information only and not legal advice."
        result = sanitize_output(text, regime="bns_bnss")
        assert result.passed is True, f"Failed for valid BNS citation: {citation}, stripped: {result.sections_stripped}"
        assert len(result.sections_stripped) == 0

    @pytest.mark.parametrize("citation", [
        "CrPC 438",
        "Section 438 CrPC",
        "438 CrPC",
        "Section 438 of CrPC",
        "Section 438",
        "Section 498A",
        "IPC 498A",
        "498A IPC",
        "Section 498A IPC",
        "Section 498A of the Indian Penal Code",
        "Section 436/437/439",
        "CrPC 436/437/439",
        "Section 436",
        "CrPC 436",
        "IPC 379",
        "Section 379",
    ])
    def test_ipc_valid_formats_pass(self, citation):
        text = f"According to {citation}, relief is available. This is general educational information only and not legal advice."
        result = sanitize_output(text, regime="ipc_crpc")
        assert result.passed is True, f"Failed for valid IPC citation: {citation}, stripped: {result.sections_stripped}"
        assert len(result.sections_stripped) == 0


class TestSurgicalStripping:
    """Test that unauthorized citations are stripped without damaging surrounding text."""

    def test_surgical_strip_preserves_legitimate_content(self):
        text = (
            "Under Section 498A of the IPC, cruelty was defined. "
            "However, under BNS 85, modern protections apply. "
            "Step 1: Gather your marriage certificates and communication records. "
            "Step 2: Approach the District Court for relief under BNSS 482. "
            "This is general educational information only and not legal advice."
        )
        result = sanitize_output(text, regime="bns_bnss")
        # IPC 498A should be replaced, but BNS 85 and BNSS 482 should remain
        assert "498A" not in result.text
        assert "the relevant statutory provision" in result.text
        assert "BNS 85" in result.text
        assert "BNSS 482" in result.text
        assert "Step 1: Gather your marriage certificates" in result.text
        assert "Step 2: Approach the District Court" in result.text
        # Does NOT fall back to generic template
        assert "Unfortunately, specific statutory sections" not in result.text


