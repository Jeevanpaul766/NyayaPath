"""
NyayaPath — Tavily Search Client

Wrapper around the Tavily API with domain whitelisting, timeout handling,
and result normalization. Only results from trusted legal domains are
used in the synthesis pipeline.
"""

from __future__ import annotations

from urllib.parse import urlparse
from src.config import TAVILY_API_KEY, TRUSTED_DOMAINS, TAVILY_MAX_RESULTS
from src.utils.logger import get_logger

logger = get_logger(__name__)


def normalize_domain(url: str) -> str:
    """Extract and normalize the domain from a URL.

    Strips protocol, 'www.' prefix, and trailing paths.

    Args:
        url: A full URL string.

    Returns:
        Normalized domain string (e.g., 'indiankanoon.org').
    """
    try:
        parsed = urlparse(url)
        domain = parsed.netloc or parsed.path.split("/")[0]
        # Strip www. prefix
        if domain.startswith("www."):
            domain = domain[4:]
        return domain.lower()
    except Exception:
        return ""


def is_trusted_domain(url: str, trusted_domains: list[str] | None = None) -> bool:
    """Check if a URL belongs to a trusted domain.

    Supports exact matches and subdomain matches
    (e.g., 'docs.indiankanoon.org' matches 'indiankanoon.org').

    Args:
        url: The URL to check.
        trusted_domains: Domain whitelist. Defaults to TRUSTED_DOMAINS.

    Returns:
        True if the URL's domain is trusted.
    """
    domains = trusted_domains or TRUSTED_DOMAINS
    normalized = normalize_domain(url)
    if not normalized:
        return False

    for trusted in domains:
        trusted_clean = trusted.lower().replace("www.", "")
        if normalized == trusted_clean or normalized.endswith(f".{trusted_clean}"):
            return True
    return False


def search_tavily(
    query: str,
    max_results: int = TAVILY_MAX_RESULTS,
    include_domains: list[str] | None = None,
) -> list[dict]:
    """Execute a domain-restricted Tavily search.

    Args:
        query: The search query string.
        max_results: Maximum number of results to return.
        include_domains: Domain whitelist. Defaults to TRUSTED_DOMAINS.

    Returns:
        List of result dicts with keys: title, url, content, score, domain.
        Returns empty list on failure.
    """
    if not TAVILY_API_KEY or TAVILY_API_KEY == "tvly-your-key-here":
        logger.warning("Tavily API key not configured — skipping search")
        return []

    domains = include_domains or TRUSTED_DOMAINS

    try:
        from tavily import TavilyClient

        client = TavilyClient(api_key=TAVILY_API_KEY)
        response = client.search(
            query=query,
            max_results=max_results,
            include_domains=domains,
            search_depth="advanced",
        )

        results = []
        for item in response.get("results", []):
            url = item.get("url", "")
            domain = normalize_domain(url)

            results.append({
                "title": item.get("title", ""),
                "url": url,
                "content": item.get("content", ""),
                "score": item.get("score", 0.0),
                "domain": domain,
            })

        logger.info(f"Tavily returned {len(results)} results for: {query[:60]}...")
        return results

    except Exception as exc:
        logger.error(f"Tavily search failed: {exc}")
        return []

