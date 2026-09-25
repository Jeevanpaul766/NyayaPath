"""
NyayaPath — Free Legal Aid Directory

Hard-coded institutional legal aid pathways. This information is
always surfaced in every guidance response regardless of the issue
category or code regime.

All data is manually verified. The LLM never generates these
details — they are injected deterministically.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class LegalAidResource:
    """A single legal aid institution or helpline."""

    name: str
    description: str
    helpline: str | None = None
    website: str | None = None
    notes: str = ""


# ---------------------------------------------------------------------------
# Institutional Directory
# ---------------------------------------------------------------------------

NALSA = LegalAidResource(
    name="National Legal Services Authority (NALSA)",
    description=(
        "NALSA provides free legal services to eligible persons under "
        "the Legal Services Authorities Act, 1987 (Section 12). "
        "Eligible categories include women, children, persons in custody, "
        "SC/ST communities, industrial workmen, victims of disasters / "
        "trafficking, persons with disabilities, and persons whose annual "
        "income is below the prescribed threshold."
    ),
    helpline="15100",
    website="https://nalsa.gov.in",
    notes="Toll-free helpline operational across India.",
)

SLSA = LegalAidResource(
    name="State Legal Services Authority (SLSA)",
    description=(
        "Each state has a Legal Services Authority that coordinates "
        "free legal aid at the state level. Contact your SLSA for "
        "local panel lawyers and legal aid clinics."
    ),
    website="https://nalsa.gov.in/lsa/state-legal-services-authorities",
)

NALSA_LOCATOR = LegalAidResource(
    name="NALSA Legal Services Locator",
    description=(
        "Use the official NALSA locator to find the nearest Legal "
        "Services Authority, Lok Adalat, or legal aid clinic."
    ),
    website="https://nalsa.gov.in/legal-services/find-legal-services-authority",
)


# ---------------------------------------------------------------------------
# Aggregated list for deterministic injection
# ---------------------------------------------------------------------------

LEGAL_AID_RESOURCES: list[LegalAidResource] = [NALSA, SLSA, NALSA_LOCATOR]


def format_legal_aid_block() -> str:
    """Return a pre-formatted markdown block for the 'Free Legal Aid' section.

    This block is deterministically appended to every guidance response.
    """
    lines = [
        "You may be entitled to **free legal aid**. The following resources "
        "can help:\n",
    ]

    for res in LEGAL_AID_RESOURCES:
        lines.append(f"- **{res.name}**")
        if res.helpline:
            lines.append(f"  - Helpline: **{res.helpline}** (toll-free)")
        if res.website:
            lines.append(f"  - Website: {res.website}")
        if res.notes:
            lines.append(f"  - {res.notes}")

    lines.append(
        "\nUnder the Legal Services Authorities Act 1987, eligible persons "
        "— including women, persons in custody, SC/ST communities, and "
        "those below prescribed income thresholds — are entitled to free "
        "legal representation."
    )

    return "\n".join(lines)
