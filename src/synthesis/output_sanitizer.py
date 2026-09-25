"""
NyayaPath — Deterministic Output Sanitizer (FR-6)

Zero-LLM rule-based validator that checks synthesized guidance for:
  1. Disclaimer presence
  2. Outcome prediction language (prohibited)
  3. Section number allowlist compliance (regime-isolated)

Features:
  - Preserves statute enactment years (e.g., 2023, 1860, 1973, 1881) in Act names.
  - Recognizes diverse valid citation formats:
      • "Section 318" / "Sec. 438" / "u/s 420"
      • "BNS 318" / "CrPC 438" / "IPC 498A" / "BNSS 482"
      • "318 BNS" / "438 CrPC" / "498A IPC"
      • "Section 318 of BNS" / "Section 438 of CrPC"
      • "Section 318 of the Bharatiya Nyaya Sanhita, 2023"
      • Multi-slash bail provisions: "436/437/439" / "CrPC 436/437/439"
      • Subsections: "BNS 318(4)" / "Section 318(4)" / "BNSS 175(3)"
  - Enforces strict cross-regime isolation:
      • In 'bns_bnss' regime: IPC/CrPC citations are blocked.
      • In 'ipc_crpc' regime: BNS/BNSS citations are blocked.
  - Non-destructive surgical stripping: replaces only unauthorized citation spans
    with "the relevant statutory provision", preserving legitimate guidance,
    authorized sections, and surrounding text.

This module is the final quality gate before user-facing output.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional, List, Tuple

from src.config import DISCLAIMER_CHECK_PHRASE
from src.knowledge.legal_mappings import (
    get_allowlist_sections,
    get_allowlist_for_regime,
    _get_base_section,
)
from src.utils.logger import get_logger

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Check Result
# ---------------------------------------------------------------------------

@dataclass
class SanitizationResult:
    """Result of the output sanitization pipeline."""

    passed: bool
    text: str
    checks_failed: list[str]
    sections_stripped: list[str]


# ---------------------------------------------------------------------------
# Check 1: Disclaimer Verification
# ---------------------------------------------------------------------------

def _check_disclaimer(text: str) -> bool:
    """Verify the required disclaimer phrase is present."""
    return DISCLAIMER_CHECK_PHRASE.lower() in text.lower()


# ---------------------------------------------------------------------------
# Check 2: Outcome Prediction Detection
# ---------------------------------------------------------------------------

_OUTCOME_PATTERN = re.compile(
    r"\b("
    r"you\s+will\s+(?:definitely\s+)?(?:win|succeed|get\s+(?:acquitted|off))"
    r"|guaranteed\s+(?:acquittal|bail|result)"
    r"|charges?\s+will\s+(?:definitely\s+)?be\s+dropped"
    r"|sure\s+to\s+get\s+bail"
    r"|judge\s+will\s+(?:definitely\s+)?dismiss"
    r"|100\s*%"
    r"|guaranteed"
    r"|certain\s+to\s+(?:win|succeed|get)"
    r"|no\s+chance\s+of\s+conviction"
    r"|case\s+will\s+(?:definitely\s+)?be\s+(?:dismissed|thrown\s+out)"
    r")",
    re.IGNORECASE,
)


def _check_no_outcome_predictions(text: str) -> tuple[bool, list[str]]:
    """Check that the text contains no outcome predictions.

    Returns:
        Tuple of (passed, list_of_matches).
    """
    matches = _OUTCOME_PATTERN.findall(text)
    return len(matches) == 0, matches


# ---------------------------------------------------------------------------
# Check 3: Section Number Citation Parsing & Allowlist Enforcement
# ---------------------------------------------------------------------------

@dataclass
class SectionCitation:
    """Structured representation of a detected statutory citation in text."""

    raw: str
    """Exact substring matched in the source text (e.g. 'Section 318 of BNS')."""

    code: Optional[str]
    """Canonical statute code ('IPC', 'CRPC', 'BNS', 'BNSS', 'BSA', 'NI ACT', or None)."""

    section: str
    """Extracted section identifier (e.g. '318', '318(4)', '438', '436/437/439')."""

    start: int
    """Start character offset in source text."""

    end: int
    """End character offset in source text."""


def _is_year(val: str) -> bool:
    """Return True if a string represents a 4-digit calendar or statute enactment year.

    In Indian criminal law:
      - IPC max section is 511
      - CrPC max section is 484
      - BNS max section is 358
      - BNSS max section is 531
      - BSA max section is 170
      - NI Act max section is 148

    No criminal statute in India has a 4-digit section number. Any 4-digit
    number between 1800 and 2099 (e.g. 1860, 1881, 1973, 2023, 2024) is an
    enactment year or calendar year and MUST NOT be treated as a section number.
    """
    val_clean = val.strip()
    if val_clean.isdigit() and len(val_clean) == 4:
        y = int(val_clean)
        if 1800 <= y <= 2099:
            return True
    return False


# Recognized statute name aliases mapped to canonical uppercase codes
_CODE_CANONICAL: dict[str, str] = {
    "IPC": "IPC",
    "I.P.C.": "IPC",
    "INDIAN PENAL CODE": "IPC",
    "CRPC": "CRPC",
    "CR.P.C.": "CRPC",
    "CODE OF CRIMINAL PROCEDURE": "CRPC",
    "BNS": "BNS",
    "BHARATIYA NYAYA SANHITA": "BNS",
    "BNSS": "BNSS",
    "BHARATIYA NAGARIK SURAKSHA SANHITA": "BNSS",
    "BSA": "BSA",
    "BHARATIYA SAKSHYA ADHINIYAM": "BSA",
    "NI ACT": "NI ACT",
    "N.I. ACT": "NI ACT",
    "NEGOTIABLE INSTRUMENTS ACT": "NI ACT",
}

_CODE_PATTERN = (
    r"(?:BNS|BNSS|IPC|CrPC|Cr\.P\.C\.|I\.P\.C\.|BSA|NI\s+Act|"
    r"Bharatiya\s+Nyaya\s+Sanhita|Indian\s+Penal\s+Code|Code\s+of\s+Criminal\s+Procedure|"
    r"Bharatiya\s+Nagarik\s+Suraksha\s+Sanhita|Bharatiya\s+Sakshya\s+Adhiniyam|"
    r"Negotiable\s+Instruments\s+Act)"
)

# Supports single sections with letters and subsections: '498A', '318(4)', '156(3)'
# as well as slash-separated bail sections: '436/437/439', '478/480/483'
_SEC_PATTERN = r"(?:\d+(?:/\d+)+|\d+[A-Za-z]?\(\d+[A-Za-z]?\)|\d+[A-Za-z]?)"

# Pattern 1: Code first — e.g. "BNS 318", "CrPC 438", "NI Act 138", "BNS Section 318"
_P_CODE_FIRST = re.compile(
    rf"\b(?P<code>{_CODE_PATTERN})\s*(?:,?\s*(?:Section|Sec\.?|Sections|Secs\.?|u/s)\s*)?(?P<sec>{_SEC_PATTERN})(?!\w)",
    re.IGNORECASE,
)

# Pattern 2: Section first with Code — e.g. "Section 318 BNS", "318 BNS", "Section 438 CrPC",
# "Section 318 of BNS", "Section 318 of the Bharatiya Nyaya Sanhita, 2023"
_P_SEC_FIRST = re.compile(
    rf"\b(?:(?:Section|Sec\.?|Sections|Secs\.?|u/s)\s+)?(?P<sec>{_SEC_PATTERN})\s*(?:,\s*|\s+(?:of\s+(?:the\s+)?|under\s+(?:the\s+)?|\(?))(?P<code>{_CODE_PATTERN})\b(?:\s*,?\s*(?:18\d\d|19\d\d|20\d\d)\)?)?",
    re.IGNORECASE,
)

# Pattern 3: Bare Section Reference — e.g. "Section 318", "Section 318(4)", "Sec. 438", "u/s 420"
_P_BARE_SEC = re.compile(
    rf"\b(?:Section|Sec\.?|Sections|Secs\.?|u/s)\s+(?P<sec>{_SEC_PATTERN})(?!\w)",
    re.IGNORECASE,
)

# Pattern 4: Bare slash-separated bail numbers — e.g. "436/437/439"
_P_SLASH_SEC = re.compile(r"\b(?P<sec>\d+/\d+/\d+)\b")


def _normalize_code(code_str: Optional[str]) -> Optional[str]:
    """Normalize a matched statute code or Act name to canonical string."""
    if not code_str:
        return None
    cleaned = re.sub(r"\s+", " ", code_str.strip().upper())
    return _CODE_CANONICAL.get(cleaned, cleaned)


def _extract_citations(text: str) -> list[SectionCitation]:
    """Parse text and extract all legal section citations while ignoring enactment years."""
    raw_citations: list[SectionCitation] = []

    for pattern in (_P_CODE_FIRST, _P_SEC_FIRST, _P_BARE_SEC, _P_SLASH_SEC):
        for m in pattern.finditer(text):
            sec = m.group("sec")
            # Enactment / calendar years (e.g. 2023, 1860) are not legal section numbers
            if _is_year(sec):
                continue

            code_raw = m.groupdict().get("code")
            code = _normalize_code(code_raw)

            raw_citations.append(
                SectionCitation(
                    raw=m.group(0),
                    code=code,
                    section=sec,
                    start=m.start(),
                    end=m.end(),
                )
            )

    # Sort matches by start position ascending, then length descending
    raw_citations.sort(key=lambda c: (c.start, -(c.end - c.start)))

    # Merge overlapping citations, keeping the longest match (which contains the code)
    merged: list[SectionCitation] = []
    for c in raw_citations:
        if not merged:
            merged.append(c)
            continue
        prev = merged[-1]
        if c.start < prev.end:
            # Overlapping match: prefer the one with a recognized code or the wider span
            if (c.code and not prev.code) or (c.end > prev.end):
                merged[-1] = c
        else:
            merged.append(c)

    return merged


def _extract_section_numbers(text: str) -> list[str]:
    """Extract all section-like references from the text for allowlist checking.

    Returns bare section numbers, base sections, and code-prefixed variants.
    Enactment years (e.g., 2023 in 'Bharatiya Nyaya Sanhita, 2023') are excluded.
    """
    citations = _extract_citations(text)
    found: set[str] = set()

    for c in citations:
        sec = c.section.upper()
        found.add(sec)
        base = _get_base_section(sec).upper()
        if base != sec:
            found.add(base)
        if "/" in sec:
            for p in sec.split("/"):
                found.add(p.strip())
        if c.code:
            found.add(f"{c.code} {sec}")
            if base != sec:
                found.add(f"{c.code} {base}")
        found.add(c.raw.strip().upper())

    return list(found)


def _check_allowlist(text: str, regime: str = "ambiguous") -> tuple[bool, list[str]]:
    """Check that all section references in the text are permitted in the active regime.

    Cross-Regime Isolation Rules:
      - In 'bns_bnss': IPC and CrPC citations are strictly prohibited.
      - In 'ipc_crpc': BNS and BNSS citations are strictly prohibited.
      - In 'ambiguous': All mapped sections are permitted.
      - Unchanged statutes (e.g. NI Act 138) are permitted in all regimes.

    Args:
        text: The synthesized guidance text to check.
        regime: Code regime — 'ipc_crpc', 'bns_bnss', or 'ambiguous'.

    Returns:
        Tuple of (all_allowed, list_of_unauthorized_citations).
    """
    citations = _extract_citations(text)
    if regime in ("ipc_crpc", "bns_bnss"):
        allowlist = get_allowlist_for_regime(regime)
    else:
        allowlist = get_allowlist_sections()
    allowlist_upper = {s.upper().strip() for s in allowlist}

    unauthorized_citations: list[str] = []

    for cit in citations:
        # 1. Enactment years are not sections
        if _is_year(cit.section):
            continue

        code = cit.code

        # 2. Strict Cross-Regime Isolation Check
        if regime == "ipc_crpc" and code in ("BNS", "BNSS", "BSA"):
            unauthorized_citations.append(cit.raw)
            continue
        elif regime == "bns_bnss" and code in ("IPC", "CRPC"):
            unauthorized_citations.append(cit.raw)
            continue

        # 3. Allowlist Membership Check
        sec = cit.section.upper()
        base_sec = _get_base_section(sec).upper()

        if code:
            # Code-prefixed reference: must match in regime allowlist
            prefixed = f"{code} {sec}".upper()
            prefixed_base = f"{code} {base_sec}".upper()
            if prefixed not in allowlist_upper and prefixed_base not in allowlist_upper:
                unauthorized_citations.append(cit.raw)
        else:
            # Bare section reference: permitted if bare number, base section,
            # or any code-prefixed form is in the active regime allowlist
            is_allowed = (
                sec in allowlist_upper
                or base_sec in allowlist_upper
                or any(
                    allowed.endswith(f" {sec}") or allowed.endswith(f" {base_sec}")
                    for allowed in allowlist_upper
                )
            )
            if not is_allowed:
                unauthorized_citations.append(cit.raw)

    return len(unauthorized_citations) == 0, unauthorized_citations


# ---------------------------------------------------------------------------
# Non-Destructive Unauthorized Section Stripping
# ---------------------------------------------------------------------------

def _strip_unauthorized_sections(
    text: str,
    unauthorized: list[str] | None = None,
    regime: str = "ambiguous",
) -> str:
    """Replace unauthorized section references with generic legal language.

    Performs surgical span-based replacement of only the unauthorized citations,
    leaving legitimate text, valid citations, and Act titles/years completely intact.

    Args:
        text: Input guidance text.
        unauthorized: Optional list of unauthorized strings to strip.
        regime: Active legal regime ('ipc_crpc', 'bns_bnss', or 'ambiguous').

    Returns:
        Cleaned text with unauthorized sections replaced.
    """
    citations = _extract_citations(text)
    if regime in ("ipc_crpc", "bns_bnss"):
        allowlist = get_allowlist_for_regime(regime)
    else:
        allowlist = get_allowlist_sections()
    allowlist_upper = {s.upper().strip() for s in allowlist}

    unauth_set = {u.upper().strip() for u in (unauthorized or [])}
    to_replace: list[SectionCitation] = []

    for cit in citations:
        if _is_year(cit.section):
            continue

        is_unauth = False
        # If an explicit unauthorized list was provided, match against it
        if unauth_set and (
            cit.raw.upper().strip() in unauth_set
            or cit.section.upper().strip() in unauth_set
            or (cit.code and f"{cit.code} {cit.section}".upper().strip() in unauth_set)
        ):
            is_unauth = True
        else:
            # Check regime isolation and allowlist
            code = cit.code
            if regime == "ipc_crpc" and code in ("BNS", "BNSS", "BSA"):
                is_unauth = True
            elif regime == "bns_bnss" and code in ("IPC", "CRPC"):
                is_unauth = True
            else:
                sec = cit.section.upper()
                base_sec = _get_base_section(sec).upper()
                if code:
                    prefixed = f"{code} {sec}".upper()
                    prefixed_base = f"{code} {base_sec}".upper()
                    if prefixed not in allowlist_upper and prefixed_base not in allowlist_upper:
                        is_unauth = True
                else:
                    if not (
                        sec in allowlist_upper
                        or base_sec in allowlist_upper
                        or any(
                            allowed.endswith(f" {sec}") or allowed.endswith(f" {base_sec}")
                            for allowed in allowlist_upper
                        )
                    ):
                        is_unauth = True

        if is_unauth:
            to_replace.append(cit)

    # Perform span replacements from back to front so character indices remain stable
    result = text
    for cit in sorted(to_replace, key=lambda c: c.start, reverse=True):
        result = result[:cit.start] + "the relevant statutory provision" + result[cit.end:]

    # Fallback cleanup for any strings passed in 'unauthorized' that weren't caught by spans
    if unauthorized:
        for u in unauthorized:
            if not _is_year(u):
                escaped = re.escape(u.strip())
                result = re.sub(
                    rf"\b(?:(?:Section|Sec\.?)\s+)?{escaped}\b",
                    "the relevant statutory provision",
                    result,
                    flags=re.IGNORECASE,
                )

    return result


# ---------------------------------------------------------------------------
# Add Missing Disclaimer
# ---------------------------------------------------------------------------

_DEFAULT_DISCLAIMER = (
    "\n\n---\n"
    "*This is general educational information only and not legal advice. "
    "Every case is different. You must consult a qualified advocate "
    "before taking any step.*"
)


def _ensure_disclaimer(text: str) -> str:
    """Append the disclaimer if it's missing."""
    if _check_disclaimer(text):
        return text
    return text + _DEFAULT_DISCLAIMER


_INSTRUCTION_ARTIFACT_PATTERNS = [
    re.compile(r"^\s*A practical chronological roadmap for the citizen:?\s*$", re.MULTILINE | re.IGNORECASE),
    re.compile(r"^\s*Categorized checklist using checkbox bullets:?\s*$", re.MULTILINE | re.IGNORECASE),
    re.compile(r"^\s*Provide concrete legal aid access details:?\s*$", re.MULTILINE | re.IGNORECASE),
    re.compile(r"^\s*Explain the formal statutory legal remedies:?\s*$", re.MULTILINE | re.IGNORECASE),
]


def _clean_instruction_artifacts(text: str) -> str:
    """Strip accidental model echoes of prompt instruction labels."""
    for pat in _INSTRUCTION_ARTIFACT_PATTERNS:
        text = pat.sub("", text)
    # Collapse excess empty lines
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


# ---------------------------------------------------------------------------
# Main Sanitization Pipeline
# ---------------------------------------------------------------------------

def sanitize_output(text: str, regime: str = "ambiguous") -> SanitizationResult:
    """Run the full deterministic output sanitization pipeline.

    This is a zero-LLM check. It uses only regex and string matching.

    Pipeline:
        1. Check disclaimer → add if missing
        2. Check outcome predictions → flag if found and replace with standard caution
        3. Check section allowlist → strip unauthorized sections surgically and re-check

    Args:
        text: The raw synthesized guidance text.
        regime: Code regime for section allowlist filtering.
            When ``'ipc_crpc'``, only IPC/CrPC sections are allowed.
            When ``'bns_bnss'``, only BNS/BNSS sections are allowed.
            When ``'ambiguous'``, all mapped sections are allowed.

    Returns:
        A :class:`SanitizationResult` with the sanitized text and metadata.
    """
    checks_failed: list[str] = []
    sections_stripped: list[str] = []

    # --- Step 1: Ensure disclaimer ---
    text = _ensure_disclaimer(text)

    # --- Step 2: Check outcome predictions ---
    no_predictions, prediction_matches = _check_no_outcome_predictions(text)
    if not no_predictions:
        checks_failed.append(f"outcome_predictions: {prediction_matches}")
        # Remove the offending phrases
        for match in prediction_matches:
            text = text.replace(match, "[outcome cannot be predicted]")
        logger.warning(f"Stripped outcome predictions: {prediction_matches}")

    # --- Step 3: Check section allowlist (regime-specific) ---
    all_allowed, unauthorized = _check_allowlist(text, regime)
    if not all_allowed:
        checks_failed.append(f"unauthorized_sections: {unauthorized}")
        sections_stripped.extend(unauthorized)
        logger.warning(f"Stripping unauthorized sections: {unauthorized}")

        # Surgically strip unauthorized references
        text = _strip_unauthorized_sections(text, unauthorized, regime=regime)

        # Re-check after stripping
        all_allowed_retry, still_unauthorized = _check_allowlist(text, regime)
        if not all_allowed_retry:
            logger.error(
                f"Still unauthorized after strip: {still_unauthorized}. "
                f"Falling back to no-sections template."
            )
            # Import here to avoid circular imports
            from src.synthesis.fallback_templates import get_no_sections_fallback
            text = get_no_sections_fallback()
            return SanitizationResult(
                passed=False,
                text=text,
                checks_failed=checks_failed,
                sections_stripped=sections_stripped + still_unauthorized,
            )

    passed = len(checks_failed) == 0
    text = _clean_instruction_artifacts(text)
    return SanitizationResult(
        passed=passed,
        text=text,
        checks_failed=checks_failed,
        sections_stripped=sections_stripped,
    )
