"""
NyayaPath — Code Regime Classifier

Determines whether IPC/CrPC or BNS/BNSS applies based on the offence
date (substantive law) and FIR date (procedural context).

Core rule:
    Substantive law is determined by WHEN THE OFFENCE WAS COMMITTED.
    • Before 1 July 2024  →  IPC / CrPC  (``ipc_crpc``)
    • On or after 1 July 2024  →  BNS / BNSS  (``bns_bnss``)
    • Straddling, unknown, or continuing  →  ``ambiguous``

    Procedural actions initiated today generally follow BNSS regardless,
    but the substantive charge sheet follows the offence-date regime.
"""

from __future__ import annotations

import re
import datetime
from src.config import CODE_TRANSITION_DATE
from src.state import CodeRegime
from src.utils.logger import get_logger

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Date Parsing
# ---------------------------------------------------------------------------

_MONTH_MAP = {
    "january": 1, "jan": 1,
    "february": 2, "feb": 2,
    "march": 3, "mar": 3,
    "april": 4, "apr": 4,
    "may": 5,
    "june": 6, "jun": 6,
    "july": 7, "jul": 7,
    "august": 8, "aug": 8,
    "september": 9, "sep": 9, "sept": 9,
    "october": 10, "oct": 10,
    "november": 11, "nov": 11,
    "december": 12, "dec": 12,
}

# Patterns: "March 2024", "2024", "last month", "few months ago",
# "July 2024", "01/07/2024", "2024-07-01", etc.
_YEAR_PATTERN = re.compile(r"\b(20\d{2})\b")
_MONTH_YEAR_PATTERN = re.compile(
    r"\b(" + "|".join(_MONTH_MAP.keys()) + r")\s+(20\d{2})\b",
    re.IGNORECASE,
)
_DATE_ISO_PATTERN = re.compile(r"\b(20\d{2})[-/](\d{1,2})[-/](\d{1,2})\b")
_DATE_DMY_PATTERN = re.compile(r"\b(\d{1,2})[-/](\d{1,2})[-/](20\d{2})\b")


def parse_approximate_date(text: str) -> datetime.date | None:
    """Extract an approximate date from natural language text.

    Returns the first recognizable date, or None if nothing is parseable.
    For month+year, defaults to the 1st of that month.
    For year-only, defaults to July 1 of that year (mid-year estimate).
    """
    if not text:
        return None

    text_lower = text.strip().lower()

    # Try ISO date: 2024-07-01
    m = _DATE_ISO_PATTERN.search(text_lower)
    if m:
        try:
            return datetime.date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
        except ValueError:
            pass

    # Try DD/MM/YYYY
    m = _DATE_DMY_PATTERN.search(text_lower)
    if m:
        try:
            return datetime.date(int(m.group(3)), int(m.group(2)), int(m.group(1)))
        except ValueError:
            pass

    # Try "Month Year"
    m = _MONTH_YEAR_PATTERN.search(text_lower)
    if m:
        month_num = _MONTH_MAP[m.group(1).lower()]
        year = int(m.group(2))
        return datetime.date(year, month_num, 1)

    # Try bare year
    m = _YEAR_PATTERN.search(text_lower)
    if m:
        year = int(m.group(1))
        return datetime.date(year, 7, 1)  # Mid-year estimate

    return None


# ---------------------------------------------------------------------------
# Relative Time Detection
# ---------------------------------------------------------------------------

_RECENT_PHRASES = re.compile(
    r"(last\s+(?:month|week|few\s+(?:days|weeks|months))|"
    r"recently|this\s+(?:month|year)|a\s+(?:few|couple)\s+(?:months?|weeks?)\s+ago)",
    re.IGNORECASE,
)

_OLD_PHRASES = re.compile(
    r"(years?\s+ago|long\s+time\s+ago|back\s+in\s+20(?:1\d|2[0-3])|"
    r"(?:before|prior\s+to)\s+(?:the\s+)?(?:new\s+)?(?:code|law|bns))",
    re.IGNORECASE,
)


def detect_temporal_hints(text: str) -> str | None:
    """Detect relative temporal language and return a hint.

    Returns:
        'recent' if events seem post-cutoff, 'old' if pre-cutoff,
        None if indeterminate.
    """
    if _RECENT_PHRASES.search(text):
        return "recent"
    if _OLD_PHRASES.search(text):
        return "old"
    return None


# ---------------------------------------------------------------------------
# Core Regime Determination
# ---------------------------------------------------------------------------

def determine_regime(
    offence_date: str | None,
    fir_date: str | None,
    user_story: str = "",
) -> tuple[CodeRegime, str]:
    """Determine the applicable code regime.

    Args:
        offence_date: User-provided approximate offence date (free text).
        fir_date: User-provided FIR registration date (free text).
        user_story: The full user narrative for temporal hint extraction.

    Returns:
        Tuple of (regime, explanation_text).
    """
    parsed_offence = parse_approximate_date(offence_date) if offence_date else None
    parsed_fir = parse_approximate_date(fir_date) if fir_date else None

    # If no explicit dates provided, attempt extraction from the user story
    if not parsed_offence and user_story:
        # Stage 1: Try keyword-anchored extraction (high confidence — the date
        # is near an action/event keyword, so it's likely the offence date)
        offence_m = re.search(
            r"(?:incident|offence|event|alleged|happened|occurred|took\s+place|"
            r"cheated|assaulted|threatened|attacked|filed|registered|arrested|"
            r"beaten|abused|harassed|robbed|stole|murdered|killed|committed)"
            r"[^.\n]*?\b([a-zA-Z0-9\s,\-/]+?\b20\d{2}\b)",
            user_story,
            re.IGNORECASE,
        )
        if offence_m:
            parsed_offence = parse_approximate_date(offence_m.group(1))

        # Stage 2: If keyword-anchored fails, try broad patterns on the full text
        # Look for "in <Month> <Year>", "<Month> <Year>", "on DD/MM/YYYY", etc.
        if not parsed_offence:
            # Try "in Month Year" pattern first (common in natural speech)
            in_month_m = re.search(
                r"\bin\s+((?:jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|"
                r"may|june?|july?|aug(?:ust)?|sep(?:t(?:ember)?)?|oct(?:ober)?|"
                r"nov(?:ember)?|dec(?:ember)?)\s+20\d{2})\b",
                user_story,
                re.IGNORECASE,
            )
            if in_month_m:
                parsed_offence = parse_approximate_date(in_month_m.group(1))

        if not parsed_offence:
            # Stage 3: Try any date-like pattern anywhere in the text
            parsed_offence = parse_approximate_date(user_story)

    if not parsed_fir and user_story:
        fir_m = re.search(
            r"(?:fir|complaint|case\s+filed|registered)[^.\n]*?\b([a-zA-Z0-9\s,\-/]+?\b20\d{2}\b)",
            user_story,
            re.IGNORECASE,
        )
        if fir_m:
            parsed_fir = parse_approximate_date(fir_m.group(1))

    # Case 1: Clear offence date available
    if parsed_offence:
        if parsed_offence < CODE_TRANSITION_DATE:
            return "ipc_crpc", (
                f"The events you described took place around {parsed_offence.strftime('%B %Y')}, "
                f"which is before the 1 July 2024 code transition. The substantive provisions "
                f"of the Indian Penal Code (IPC) and procedural framework of the Code of "
                f"Criminal Procedure (CrPC) apply to this situation."
            )
        else:
            return "bns_bnss", (
                f"The events you described took place around {parsed_offence.strftime('%B %Y')}, "
                f"which is on or after the 1 July 2024 code transition. The Bharatiya Nyaya "
                f"Sanhita (BNS) and Bharatiya Nagarik Suraksha Sanhita (BNSS) apply."
            )

    # Case 2: No offence date but FIR date + temporal hints from story
    temporal_hint = detect_temporal_hints(user_story)

    if parsed_fir:
        if parsed_fir < CODE_TRANSITION_DATE and temporal_hint != "recent":
            return "ipc_crpc", (
                f"The FIR was registered around {parsed_fir.strftime('%B %Y')}, before the "
                f"1 July 2024 transition. Based on the timeline described, IPC/CrPC likely applies."
            )
        elif parsed_fir >= CODE_TRANSITION_DATE and temporal_hint == "recent":
            return "bns_bnss", (
                f"The FIR was registered around {parsed_fir.strftime('%B %Y')}, after the "
                f"1 July 2024 transition, and the events described appear recent. BNS/BNSS applies."
            )

    # Case 3: Temporal hints only (no parsed dates)
    if temporal_hint == "recent":
        # If the current date is well past the cutoff and events are "recent",
        # it's likely BNS/BNSS — but flag with lower confidence
        today = datetime.date.today()
        if today >= datetime.date(2025, 1, 1):
            return "bns_bnss", (
                "Based on the timeline described (recent events), it appears the Bharatiya "
                "Nyaya Sanhita (BNS) and BNSS likely apply, as these events occurred after "
                "the 1 July 2024 transition. However, the exact dates should be confirmed."
            )

    # Case 4: Ambiguous — insufficient temporal information
    return "ambiguous", (
        "Based on the information provided, it is not possible to definitively determine "
        "whether the Indian Penal Code (IPC/CrPC) or the Bharatiya Nyaya Sanhita (BNS/BNSS) "
        "applies. The applicable law depends primarily on when the alleged offence was "
        "committed — not just when the FIR was registered.\n\n"
        "If the offence occurred before 1 July 2024, substantive provisions of IPC apply. "
        "If on or after 1 July 2024, BNS applies. For continuing offences that straddle "
        "the transition, both codes may be relevant, and a qualified legal practitioner "
        "will determine the applicable provisions based on the specific facts."
    )


def needs_date_clarification(
    offence_date: str | None,
    fir_date: str | None,
    user_story: str = "",
) -> bool:
    """Return True if the agent should ask clarifying date questions.

    Clarification is needed when we cannot determine the regime from
    the available information.
    """
    regime, _ = determine_regime(offence_date, fir_date, user_story)
    # If we could determine a clear regime, no need to ask
    if regime in ("ipc_crpc", "bns_bnss"):
        return False
    # Even for ambiguous, if we have SOME date info, don't ask again
    if offence_date or fir_date:
        return False
    # No dates at all — need to ask
    return True
