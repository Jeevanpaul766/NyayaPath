"""
NyayaPath — Legal Provision Mapping Table

Hand-verified mapping of IPC/CrPC provisions to their BNS/BNSS equivalents
following the 1 July 2024 criminal law transition.

IMPORTANT:
    Every entry is manually verified against indiacode.nic.in and
    date-stamped. The LLM NEVER generates section numbers — it may only
    reference sections that exist in this table. If a provision is not
    here, the fallback rule applies (plain-language description, no
    section numbers, escalate to lawyer).

Critical Collision Note:
    "Section 482" means *completely different things* under the old and
    new codes:
      • CrPC 482  = Inherent powers of the High Court (quashing)
      • BNSS 482  = Anticipatory bail (was CrPC 438)
    The agent must NEVER confuse these. The mapping table is the single
    source of truth that prevents this conflation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, Literal


# ---------------------------------------------------------------------------
# Data Model
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ProvisionMapping:
    """A single hand-verified provision transition record."""

    old_code: str
    """Source code, e.g. 'IPC' or 'CrPC'."""

    old_section: str
    """Section under the old code, e.g. '498A' or '438'."""

    description: str
    """Plain-language description of the offence or procedure."""

    new_code: Optional[str] = None
    """Target code under the new regime, e.g. 'BNS' or 'BNSS'. None if unchanged."""

    new_section: Optional[str] = None
    """Section under the new code, e.g. '85'. None if unchanged."""

    statutory_notes: str = ""
    """Additional clarifications (e.g. 'Cruelty defined in BNS 86')."""

    verified_against: str = "indiacode.nic.in"
    """Source used for verification."""

    verified_on: str = "2024-09-18"
    """Date of last manual verification (YYYY-MM-DD)."""

    status: Literal["transitioned", "unchanged"] = "transitioned"
    """Whether the provision has moved to the new code or remains unchanged."""

    offence_or_procedure: Literal["substantive", "procedural", "special_statute"] = "substantive"
    """Classification for regime-determination logic."""


# ---------------------------------------------------------------------------
# The Mapping Table (14 provisions + 1 unchanged special statute)
# ---------------------------------------------------------------------------

PROVISION_TABLE: list[ProvisionMapping] = [
    # --- Substantive Offences (IPC → BNS) ---
    ProvisionMapping(
        old_code="IPC",
        old_section="498A",
        description="Cruelty by husband or relatives of husband",
        new_code="BNS",
        new_section="85",
        statutory_notes="Cruelty defined under BNS 86",
        offence_or_procedure="substantive",
    ),
    ProvisionMapping(
        old_code="IPC",
        old_section="420",
        description="Cheating and dishonestly inducing delivery of property",
        new_code="BNS",
        new_section="318(4)",
        offence_or_procedure="substantive",
    ),
    ProvisionMapping(
        old_code="IPC",
        old_section="406",
        description="Criminal breach of trust",
        new_code="BNS",
        new_section="316",
        offence_or_procedure="substantive",
    ),
    ProvisionMapping(
        old_code="IPC",
        old_section="323",
        description="Voluntarily causing hurt",
        new_code="BNS",
        new_section="115(2)",
        offence_or_procedure="substantive",
    ),
    ProvisionMapping(
        old_code="IPC",
        old_section="324",
        description="Voluntarily causing hurt by dangerous weapons or means",
        new_code="BNS",
        new_section="118(1)",
        offence_or_procedure="substantive",
    ),
    ProvisionMapping(
        old_code="IPC",
        old_section="325",
        description="Voluntarily causing grievous hurt",
        new_code="BNS",
        new_section="116",
        offence_or_procedure="substantive",
    ),
    ProvisionMapping(
        old_code="IPC",
        old_section="354",
        description="Assault or criminal force to woman with intent to outrage modesty",
        new_code="BNS",
        new_section="74",
        offence_or_procedure="substantive",
    ),
    ProvisionMapping(
        old_code="IPC",
        old_section="506",
        description="Criminal intimidation",
        new_code="BNS",
        new_section="351(2)",
        offence_or_procedure="substantive",
    ),

    # --- Procedural Provisions (CrPC → BNSS) ---
    ProvisionMapping(
        old_code="CrPC",
        old_section="154",
        description="Information in cognizable cases (FIR registration)",
        new_code="BNSS",
        new_section="173",
        offence_or_procedure="procedural",
    ),
    ProvisionMapping(
        old_code="CrPC",
        old_section="156(3)",
        description="Magistrate's power to order investigation",
        new_code="BNSS",
        new_section="175(3)",
        offence_or_procedure="procedural",
    ),
    ProvisionMapping(
        old_code="CrPC",
        old_section="41A",
        description="Notice of appearance before police officer",
        new_code="BNSS",
        new_section="35(3)",
        statutory_notes="Renamed and restructured under BNSS",
        offence_or_procedure="procedural",
    ),
    ProvisionMapping(
        old_code="CrPC",
        old_section="438",
        description="Direction for grant of bail to person apprehending arrest (Anticipatory Bail)",
        new_code="BNSS",
        new_section="482",
        statutory_notes=(
            "CRITICAL: BNSS 482 = Anticipatory Bail. "
            "Do NOT confuse with old CrPC 482 (High Court inherent powers), "
            "which is now BNSS 528."
        ),
        offence_or_procedure="procedural",
    ),
    ProvisionMapping(
        old_code="CrPC",
        old_section="482",
        description="Inherent powers of High Court (quashing of proceedings)",
        new_code="BNSS",
        new_section="528",
        statutory_notes=(
            "Old CrPC 482 (quashing) is now BNSS 528. "
            "BNSS 482 is anticipatory bail (was CrPC 438)."
        ),
        offence_or_procedure="procedural",
    ),
    ProvisionMapping(
        old_code="CrPC",
        old_section="436/437/439",
        description="Bail provisions (bailable offences / non-bailable / special powers of High Court or Sessions Court)",
        new_code="BNSS",
        new_section="478/480/483",
        offence_or_procedure="procedural",
    ),

    # --- Unchanged Special Statute ---
    ProvisionMapping(
        old_code="NI Act",
        old_section="138",
        description="Dishonour of cheque for insufficiency of funds",
        new_code=None,
        new_section=None,
        statutory_notes="Negotiable Instruments Act 1881 — not part of IPC/BNS transition; remains unchanged",
        status="unchanged",
        offence_or_procedure="special_statute",
    ),

    # --- Additional Transitioned Substantive Offence (Theft) ---
    ProvisionMapping(
        old_code="IPC",
        old_section="379",
        description="Punishment for theft",
        new_code="BNS",
        new_section="303(2)",
        statutory_notes="Theft defined under BNS 303(1), punishment under BNS 303(2)",
        offence_or_procedure="substantive",
    ),
]


# ---------------------------------------------------------------------------
# Lookup Helpers & Allowlist Generation
# ---------------------------------------------------------------------------

def _get_base_section(sec: str) -> str:
    """Extract the base section from a section with a subsection (e.g., '318(4)' -> '318')."""
    import re
    m = re.match(r"^(\d+[A-Za-z]?)\(\d+[A-Za-z]?\)$", sec.strip())
    if m:
        return m.group(1)
    return sec.strip()


def _expand_section_variants(code: Optional[str], section: str) -> set[str]:
    """Expand a section into its canonical variants (bare, code-prefixed, base section, slash parts)."""
    variants: set[str] = set()
    s = section.strip()
    variants.add(s)
    if code:
        variants.add(f"{code} {s}")

    # Handle multi-section slash notation (e.g. 436/437/439)
    if "/" in s:
        for part in s.split("/"):
            p_strip = part.strip()
            variants.add(p_strip)
            if code:
                variants.add(f"{code} {p_strip}")

    # Handle subsection notation (e.g. 318(4) -> 318, 156(3) -> 156)
    base = _get_base_section(s)
    if base != s:
        variants.add(base)
        if code:
            variants.add(f"{code} {base}")

    return variants


def _build_index() -> dict[str, ProvisionMapping]:
    """Build lookup indexes keyed by both old and new section identifiers."""
    index: dict[str, ProvisionMapping] = {}
    for p in PROVISION_TABLE:
        # Key by old code + section  (e.g. "IPC 498A", "CrPC 438")
        old_key = f"{p.old_code} {p.old_section}".upper()
        index[old_key] = p

        # Key by new code + section  (e.g. "BNS 85", "BNSS 482")
        if p.new_code and p.new_section:
            new_key = f"{p.new_code} {p.new_section}".upper()
            index[new_key] = p

        # Key by bare section numbers for flexible lookup
        if p.old_section.upper() not in index:
            index[p.old_section.upper()] = p
        old_base = _get_base_section(p.old_section).upper()
        if old_base not in index:
            index[old_base] = p

        if p.new_section:
            bare_new = p.new_section.upper()
            if bare_new not in index:
                index[bare_new] = p
            new_base = _get_base_section(p.new_section).upper()
            if new_base not in index:
                index[new_base] = p
            if p.new_code:
                new_base_key = f"{p.new_code} {new_base}".upper()
                if new_base_key not in index:
                    index[new_base_key] = p

    return index


_PROVISION_INDEX: dict[str, ProvisionMapping] = _build_index()


def lookup_provision(query: str) -> Optional[ProvisionMapping]:
    """Look up a provision by old or new section reference.

    Accepts formats like '498A', 'IPC 498A', 'BNS 85', 'CrPC 438', etc.

    Returns:
        The matching :class:`ProvisionMapping`, or ``None`` if not found.
    """
    return _PROVISION_INDEX.get(query.strip().upper())


def get_allowlist_sections() -> set[str]:
    """Return the full set of section identifiers the agent is allowed to mention.

    Any section number in the synthesized output that is NOT in this set
    must be stripped by the deterministic output sanitizer.
    """
    allowed: set[str] = set()
    for p in PROVISION_TABLE:
        allowed.update(_expand_section_variants(p.old_code, p.old_section))
        if p.new_section and p.new_code:
            allowed.update(_expand_section_variants(p.new_code, p.new_section))
    return allowed


def get_provisions_for_regime(regime: str) -> list[ProvisionMapping]:
    """Return provisions relevant to a specific code regime.

    Args:
        regime: One of ``'ipc_crpc'``, ``'bns_bnss'``, or ``'ambiguous'``.

    Returns:
        List of :class:`ProvisionMapping` objects.
    """
    if regime == "ipc_crpc":
        return [p for p in PROVISION_TABLE if p.status == "transitioned"]
    elif regime == "bns_bnss":
        return [p for p in PROVISION_TABLE if p.status == "transitioned"]
    else:
        # Ambiguous — return all for reference
        return list(PROVISION_TABLE)


def get_allowlist_for_regime(regime: str) -> set[str]:
    """Return the set of section identifiers allowed for a specific regime.

    Unlike :func:`get_allowlist_sections` (which returns ALL sections across
    both regimes), this function returns ONLY the sections valid for the
    given regime. This prevents the output sanitizer from accepting
    cross-regime hallucinations.

    Args:
        regime: One of ``'ipc_crpc'``, ``'bns_bnss'``, or ``'ambiguous'``.

    Returns:
        Set of allowed section identifier strings (both bare and prefixed).
    """
    allowed: set[str] = set()

    for p in PROVISION_TABLE:
        if regime == "ipc_crpc":
            # Only old-code sections
            allowed.update(_expand_section_variants(p.old_code, p.old_section))
        elif regime == "bns_bnss":
            if p.new_code and p.new_section:
                # Only new-code sections
                allowed.update(_expand_section_variants(p.new_code, p.new_section))
            elif p.status == "unchanged":
                # Unchanged statutes (e.g., NI Act 138) are allowed in any regime
                allowed.update(_expand_section_variants(p.old_code, p.old_section))
        else:
            # Ambiguous — allow everything
            allowed.update(_expand_section_variants(p.old_code, p.old_section))
            if p.new_section and p.new_code:
                allowed.update(_expand_section_variants(p.new_code, p.new_section))

    return allowed

