"""
Tests for the legal provision mapping table.

Validates:
  - Table schema integrity (all required fields present)
  - Bidirectional lookups (old → new, new → old)
  - Allowlist completeness
  - The critical 482 collision is handled correctly
  - Fallback rule (unmapped provisions return None)
"""

import pytest
from src.knowledge.legal_mappings import (
    PROVISION_TABLE,
    lookup_provision,
    get_allowlist_sections,
    get_provisions_for_regime,
    ProvisionMapping,
)


class TestProvisionTableSchema:
    """Verify that every entry in the table has valid fields."""

    def test_table_has_minimum_entries(self):
        assert len(PROVISION_TABLE) >= 14, (
            f"Table has {len(PROVISION_TABLE)} entries, need at least 14"
        )

    def test_all_entries_have_old_code_and_section(self):
        for p in PROVISION_TABLE:
            assert p.old_code, f"Missing old_code in entry: {p}"
            assert p.old_section, f"Missing old_section in entry: {p}"

    def test_all_entries_have_description(self):
        for p in PROVISION_TABLE:
            assert p.description, f"Missing description in entry: {p}"

    def test_all_entries_have_verification(self):
        for p in PROVISION_TABLE:
            assert p.verified_against, f"Missing verified_against in entry: {p}"
            assert p.verified_on, f"Missing verified_on in entry: {p}"

    def test_transitioned_entries_have_new_code(self):
        for p in PROVISION_TABLE:
            if p.status == "transitioned":
                assert p.new_code, f"Transitioned entry missing new_code: {p.old_section}"
                assert p.new_section, f"Transitioned entry missing new_section: {p.old_section}"

    def test_unchanged_entry_has_no_new_code(self):
        unchanged = [p for p in PROVISION_TABLE if p.status == "unchanged"]
        assert len(unchanged) >= 1, "Need at least one unchanged entry (NI Act 138)"
        for p in unchanged:
            assert p.new_code is None
            assert p.new_section is None


class TestLookup:
    """Test bidirectional provision lookup."""

    def test_lookup_by_old_section(self):
        result = lookup_provision("IPC 498A")
        assert result is not None
        assert result.new_section == "85"

    def test_lookup_by_new_section(self):
        result = lookup_provision("BNS 85")
        assert result is not None
        assert result.old_section == "498A"

    def test_lookup_by_bare_section(self):
        result = lookup_provision("498A")
        assert result is not None

    def test_lookup_case_insensitive(self):
        result = lookup_provision("ipc 498a")
        assert result is not None

    def test_lookup_unmapped_returns_none(self):
        result = lookup_provision("IPC 999")
        assert result is None

    def test_lookup_ni_act_138(self):
        result = lookup_provision("NI Act 138")
        assert result is not None
        assert result.status == "unchanged"
        assert result.new_code is None


class TestCritical482Collision:
    """The most important test: 482 means different things in old vs new codes."""

    def test_crpc_482_is_quashing(self):
        result = lookup_provision("CrPC 482")
        assert result is not None
        assert "quash" in result.description.lower() or "inherent" in result.description.lower()
        assert result.new_section == "528"  # BNSS 528

    def test_crpc_438_is_anticipatory_bail(self):
        result = lookup_provision("CrPC 438")
        assert result is not None
        assert "bail" in result.description.lower() or "anticipatory" in result.description.lower()
        assert result.new_section == "482"  # BNSS 482

    def test_bnss_482_is_NOT_quashing(self):
        """BNSS 482 should resolve to anticipatory bail, NOT quashing."""
        result = lookup_provision("BNSS 482")
        assert result is not None
        # BNSS 482 = Anticipatory Bail (was CrPC 438)
        assert "bail" in result.description.lower() or "anticipatory" in result.description.lower()

    def test_bnss_528_is_quashing(self):
        result = lookup_provision("BNSS 528")
        assert result is not None
        assert "quash" in result.description.lower() or "inherent" in result.description.lower()


class TestAllowlist:
    """Test the section allowlist used by the output sanitizer."""

    def test_allowlist_not_empty(self):
        allowed = get_allowlist_sections()
        assert len(allowed) > 0

    def test_allowlist_contains_key_sections(self):
        allowed = get_allowlist_sections()
        # Check a few critical ones are present
        assert any("498A" in s for s in allowed)
        assert any("85" in s for s in allowed)
        assert any("138" in s for s in allowed)

    def test_allowlist_contains_both_old_and_new(self):
        allowed = get_allowlist_sections()
        # Should have IPC sections
        assert any("IPC" in s for s in allowed)
        # Should have BNS sections
        assert any("BNS" in s for s in allowed)


class TestRegimeFilter:
    """Test provision filtering by regime."""

    def test_ipc_regime_returns_provisions(self):
        provisions = get_provisions_for_regime("ipc_crpc")
        assert len(provisions) > 0

    def test_bns_regime_returns_provisions(self):
        provisions = get_provisions_for_regime("bns_bnss")
        assert len(provisions) > 0

    def test_ambiguous_returns_all(self):
        provisions = get_provisions_for_regime("ambiguous")
        assert len(provisions) == len(PROVISION_TABLE)
