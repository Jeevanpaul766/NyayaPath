"""
NyayaPath — Search Result Grader

Evaluates the quality and relevance of Tavily search results.
Determines whether results are sufficient for synthesis or whether
a retry with a broadened query is needed.

CRITICAL: Domain trust is checked FIRST. Results from unauthorized
domains are immediately rejected regardless of keyword relevance.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from src.config import TRUSTED_DOMAINS
from src.retrieval.tavily_client import is_trusted_domain
from src.utils.logger import get_logger

logger = get_logger(__name__)

# Minimum content length (characters) to consider a result useful
_MIN_CONTENT_LENGTH = 100

# Minimum number of results with meaningful content
_MIN_USEFUL_RESULTS = 1

# Keywords that indicate legal relevance
_RELEVANCE_KEYWORDS = [
    "section", "act", "court", "bail", "fir", "complaint",
    "procedure", "accused", "offence", "ipc", "crpc", "bns",
    "bnss", "penal", "criminal", "magistrate", "police",
    "arrest", "summons", "investigation", "nalsa", "legal aid",
]


# ---------------------------------------------------------------------------
# Structured Evidence Item
# ---------------------------------------------------------------------------

@dataclass
class EvidenceItem:
    """A graded, domain-verified search result."""

    source_id: int
    title: str
    url: str
    domain: str
    is_trusted: bool
    supporting_text: str
    quality_score: float
    relevance_score: int = 0


def grade_results(results: list[dict]) -> tuple[bool, str]:
    """Grade the quality of search results.

    CRITICAL: Domain trust is enforced FIRST for Tavily results. A result
    from a non-trusted domain is immediately rejected regardless of keyword
    relevance. This prevents commercial blogs from leaking into guidance.

    Local RAG results (url starts with 'local://' or source == 'local_rag')
    are ALWAYS trusted — they are sourced from the indexed official bare acts.

    Args:
        results: List of result dicts from Tavily or local RAG.

    Returns:
        Tuple of (is_acceptable, reason).
    """
    if not results:
        return False, "No search results returned"

    useful_count = 0
    rejected_count = 0

    for r in results:
        content = r.get("content", "")
        url = r.get("url", "")

        # --- LOCAL RAG results are always trusted ---
        is_local = (
            url.startswith("local://")
            or r.get("source") == "local_rag"
        )

        if not is_local:
            # --- DOMAIN CHECK for Tavily results (mandatory) ---
            if not is_trusted_domain(url):
                rejected_count += 1
                logger.debug(f"Rejected untrusted domain: {url}")
                continue

        # Check content length
        if len(content) < _MIN_CONTENT_LENGTH:
            continue

        # Check relevance keywords (relaxed for local RAG — bare acts always qualify)
        if is_local:
            useful_count += 1
        else:
            content_lower = content.lower()
            relevance_hits = sum(
                1 for kw in _RELEVANCE_KEYWORDS if kw in content_lower
            )
            if relevance_hits >= 2:
                useful_count += 1

    if rejected_count > 0:
        logger.info(f"Domain filter: rejected {rejected_count} non-trusted results")

    if useful_count >= _MIN_USEFUL_RESULTS:
        return True, f"Found {useful_count} useful results"
    else:
        return False, f"Only {useful_count} useful results (need {_MIN_USEFUL_RESULTS})"


def grade_results_structured(results: list[dict]) -> list[EvidenceItem]:
    """Grade results and return structured EvidenceItem objects.

    Local RAG results (local:// URL or source='local_rag') are always
    trusted. Tavily results must pass the domain whitelist check.

    Args:
        results: List of result dicts from Tavily or local RAG.

    Returns:
        List of :class:`EvidenceItem` objects, sorted by quality score.
    """
    evidence: list[EvidenceItem] = []

    for i, r in enumerate(results):
        url     = r.get("url", "")
        content = r.get("content", "")

        # Local RAG results are always trusted
        is_local = url.startswith("local://") or r.get("source") == "local_rag"
        trusted  = is_local or is_trusted_domain(url)

        if not trusted:
            continue

        if len(content) < _MIN_CONTENT_LENGTH:
            continue

        content_lower  = content.lower()
        relevance      = sum(1 for kw in _RELEVANCE_KEYWORDS if kw in content_lower)

        from src.retrieval.tavily_client import normalize_domain
        domain = r.get("act", normalize_domain(url)) if is_local else normalize_domain(url)

        item = EvidenceItem(
            source_id=i,
            title=r.get("title", ""),
            url=url,
            domain=domain,
            is_trusted=True,
            supporting_text=content[:500],
            quality_score=r.get("score", 0.5 if is_local else 0.0),
            relevance_score=relevance,
        )
        evidence.append(item)

    evidence.sort(key=lambda e: e.quality_score, reverse=True)
    return evidence


# Alias for backwards compatibility
extract_evidence = grade_results_structured


def extract_sources(results: list[dict]) -> list[dict[str, str]]:
    """Extract clean source citations from search results.

    Only includes sources from trusted domains.

    Args:
        results: List of result dicts from Tavily.

    Returns:
        List of source dicts with 'title', 'url', and 'domain' keys.
    """
    sources = []
    seen_urls = set()

    for r in results:
        url = r.get("url", "")
        title = r.get("title", "")

        if url and url not in seen_urls:
            # Only include trusted domain sources
            if is_trusted_domain(url):
                from src.retrieval.tavily_client import normalize_domain
                seen_urls.add(url)
                sources.append({
                    "title": title,
                    "url": url,
                    "domain": normalize_domain(url),
                })

    return sources
