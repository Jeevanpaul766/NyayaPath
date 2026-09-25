"""
NyayaPath — Search Query Builder

Converts the agent's state variables (issue category, code regime,
identified provisions) into well-formed search queries for Tavily.
"""

from __future__ import annotations

from src.state import CodeRegime
from src.reasoning.issue_classifier import ISSUE_CATEGORIES
from src.utils.logger import get_logger

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Query Templates
# ---------------------------------------------------------------------------

_IPC_TEMPLATE = "{issue_description} procedure IPC CrPC India legal rights"
_BNS_TEMPLATE = "{issue_description} procedure Bharatiya Nyaya Sanhita BNS BNSS India legal rights"
_AMBIGUOUS_TEMPLATE = "{issue_description} procedure India criminal law 2024 transition IPC BNS"


def build_search_query(
    issue_category: str,
    code_regime: CodeRegime,
    user_story: str = "",
) -> str:
    """Build a targeted search query based on issue category and regime.

    Args:
        issue_category: One of the keys from ISSUE_CATEGORIES.
        code_regime: The determined code regime.
        user_story: The raw user story for additional context extraction.

    Returns:
        A search query string optimized for legal statutory sources.
    """
    # Get a clean issue description
    issue_desc = ISSUE_CATEGORIES.get(issue_category, "legal matter")

    # Select template based on regime
    if code_regime == "ipc_crpc":
        template = _IPC_TEMPLATE
    elif code_regime == "bns_bnss":
        template = _BNS_TEMPLATE
    else:
        template = _AMBIGUOUS_TEMPLATE

    query = template.format(issue_description=issue_desc)

    # Add specific context from common issue types
    context_additions = {
        "matrimonial_cruelty": "498A anticipatory bail mediation",
        "bail_procedure": "anticipatory bail regular bail arrest procedure",
        "quashing": "quashing High Court inherent powers FIR",
        "cheque_bounce": "Section 138 Negotiable Instruments Act cheque dishonour",
        "fir_complaint": "FIR registration police complaint magistrate",
    }

    if issue_category in context_additions:
        query += f" {context_additions[issue_category]}"

    logger.info(f"Built search query: {query[:80]}...")
    return query


def build_reformulated_query(
    original_query: str,
    issue_category: str,
    code_regime: CodeRegime,
    retry_reason: str = "",
) -> str:
    """Build an authoritative reformulated search query for retries.

    When the initial broad search returns zero or insufficient trusted results,
    this function constructs a focused query directed at official primary sources
    (such as indiacode.nic.in and prsindia.org) with bare act terminology.

    Args:
        original_query: The initial query that produced insufficient results.
        issue_category: The classified legal issue category.
        code_regime: The governing code regime (ipc_crpc, bns_bnss, ambiguous).
        retry_reason: Human-readable reason for retry triggering.

    Returns:
        A reformulated query string targeting primary statutory enactments.
    """
    issue_desc = ISSUE_CATEGORIES.get(issue_category, "criminal law")

    if code_regime == "bns_bnss":
        statute_terms = "Bharatiya Nyaya Sanhita 2023 Bharatiya Nagarik Suraksha Sanhita bare act"
    elif code_regime == "ipc_crpc":
        statute_terms = "Indian Penal Code 1860 Code of Criminal Procedure 1973 bare act"
    else:
        statute_terms = "Indian legal statutory procedure bare act"

    reformulated = f"{issue_desc} {statute_terms} site:indiacode.nic.in OR site:prsindia.org"
    logger.info(f"Built reformulated query (reason='{retry_reason}'): {reformulated[:100]}...")
    return reformulated

