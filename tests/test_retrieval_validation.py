"""
Tests for search result domain validation and evidence grading.

Validates:
  - Domain normalization correctly strips www. and protocols
  - Trusted domain check works for exact matches and subdomains
  - Commercial/unauthorized domains are rejected by the grader
  - Keyword relevance alone does NOT override domain filtering
  - extract_sources only includes trusted domains
"""

import pytest
from src.config import TRUSTED_DOMAINS
from src.retrieval.tavily_client import normalize_domain, is_trusted_domain
from src.retrieval.result_grader import grade_results, extract_sources


# Use a domain we know is in the config for testing
_FIRST_TRUSTED = TRUSTED_DOMAINS[0] if TRUSTED_DOMAINS else "indiacode.nic.in"


class TestDomainNormalization:
    """Test URL domain extraction and normalization."""

    def test_basic_url(self):
        assert normalize_domain("https://indiacode.nic.in/act/1") == "indiacode.nic.in"

    def test_www_prefix_stripped(self):
        assert normalize_domain("https://www.indiacode.nic.in/act/1") == "indiacode.nic.in"

    def test_subdomain_preserved(self):
        assert normalize_domain("https://docs.indiacode.nic.in/help") == "docs.indiacode.nic.in"

    def test_no_protocol(self):
        assert normalize_domain("indiacode.nic.in/act/456") == "indiacode.nic.in"

    def test_empty_url(self):
        assert normalize_domain("") == ""

    def test_case_insensitive(self):
        domain = normalize_domain("https://INDIACODE.NIC.IN/doc/1")
        assert domain == "indiacode.nic.in"


class TestTrustedDomainCheck:
    """Test the trusted domain checker."""

    def test_trusted_domain_exact_match(self):
        assert is_trusted_domain(
            f"https://{_FIRST_TRUSTED}/doc/123",
        ) is True

    def test_trusted_subdomain(self):
        assert is_trusted_domain(
            f"https://docs.{_FIRST_TRUSTED}/help",
        ) is True

    def test_untrusted_domain_rejected(self):
        assert is_trusted_domain(
            "https://scribd.com/legal-doc/123",
        ) is False

    def test_commercial_blog_rejected(self):
        assert is_trusted_domain(
            "https://www.lawyersclubindia.com/articles/498a-guide",
        ) is False

    def test_www_prefix_doesnt_bypass(self):
        assert is_trusted_domain(
            "https://www.scribd.com/document/legal-template",
        ) is False


class TestGradeResultsDomainFirst:
    """Test that grade_results enforces domain trust BEFORE relevance."""

    def test_rejects_high_relevance_untrusted_domain(self):
        """Even with many legal keywords, non-trusted domains are rejected."""
        results = [{
            "title": "Complete Guide to IPC 498A bail procedure",
            "url": "https://scribd.com/legal-guide-498a",
            "content": (
                "Section 498A IPC bail procedure court accused offence "
                "criminal magistrate police arrest investigation. "
                "This comprehensive legal guide covers FIR complaint "
                "procedure and anticipatory bail under CrPC 438."
            ),
            "score": 0.95,
        }]
        is_acceptable, reason = grade_results(results)
        assert is_acceptable is False, f"Untrusted domain should be rejected: {reason}"

    def test_accepts_trusted_domain_with_relevance(self):
        """Trusted domain with sufficient relevance passes."""
        results = [{
            "title": "Section 498A - India Code",
            "url": f"https://{_FIRST_TRUSTED}/act/45/section/498A",
            "content": (
                "Section 498A of the Indian Penal Code deals with cruelty "
                "by husband or his relatives towards a married woman. "
                "The court may grant bail upon consideration of the "
                "accused's circumstances and investigation status."
            ),
            "score": 0.9,
        }]
        is_acceptable, reason = grade_results(results)
        assert is_acceptable is True, f"Trusted domain should pass: {reason}"

    def test_rejects_empty_results(self):
        is_acceptable, reason = grade_results([])
        assert is_acceptable is False

    def test_rejects_short_content_from_trusted_domain(self):
        """Trusted domain but content too short should not count."""
        results = [{
            "title": "498A",
            "url": f"https://{_FIRST_TRUSTED}/doc/1",
            "content": "Short text.",
            "score": 0.8,
        }]
        is_acceptable, _ = grade_results(results)
        assert is_acceptable is False

    def test_mixed_results_only_counts_trusted(self):
        """With mixed results, only trusted domains count."""
        results = [
            {
                "title": "Scribd Legal Guide",
                "url": "https://scribd.com/doc/legal",
                "content": "Section 498A IPC bail procedure court accused " * 5,
                "score": 0.95,
            },
            {
                "title": "India Code - 498A",
                "url": f"https://{_FIRST_TRUSTED}/act/45/section/498A",
                "content": (
                    "Section 498A of the Indian Penal Code deals with cruelty "
                    "by husband or relatives. The court examines evidence."
                ),
                "score": 0.85,
            },
        ]
        is_acceptable, reason = grade_results(results)
        assert is_acceptable is True


class TestExtractSourcesDomainFiltered:
    """Test that extract_sources only includes trusted domain results."""

    def test_filters_untrusted_sources(self):
        results = [
            {"title": "India Code", "url": f"https://{_FIRST_TRUSTED}/act/1"},
            {"title": "Scribd", "url": "https://scribd.com/doc/legal"},
            {"title": "NALSA", "url": "https://nalsa.gov.in/services"},
        ]
        sources = extract_sources(results)
        urls = [s["url"] for s in sources]
        assert "https://scribd.com/doc/legal" not in urls
        assert f"https://{_FIRST_TRUSTED}/act/1" in urls
        assert "https://nalsa.gov.in/services" in urls

    def test_deduplicates_urls(self):
        results = [
            {"title": "Page 1", "url": f"https://{_FIRST_TRUSTED}/doc/1"},
            {"title": "Page 1 Dup", "url": f"https://{_FIRST_TRUSTED}/doc/1"},
        ]
        sources = extract_sources(results)
        assert len(sources) == 1

    def test_empty_results(self):
        sources = extract_sources([])
        assert sources == []
