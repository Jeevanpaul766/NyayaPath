"""
NyayaPath — Fallback Templates

Guaranteed-compliant response templates that contain ZERO section
numbers. Used when the deterministic output sanitizer cannot clean
the LLM output sufficiently.

These templates ensure the user always receives useful guidance even
in worst-case scenarios (LLM hallucination, search failure, etc.).
"""

from __future__ import annotations

from src.knowledge.legal_aid_directory import format_legal_aid_block


def get_no_sections_fallback() -> str:
    """Return a guaranteed-compliant response with no section numbers.

    This template is the nuclear option — used when the output sanitizer
    cannot clean the synthesized guidance after retry. It contains zero
    section numbers and cannot fail the allowlist check.
    """
    legal_aid = format_legal_aid_block()

    return f"""### 1. Understanding of your situation

Based on what you have described, you are facing a legal matter that involves the Indian criminal justice system. The specific provisions that apply to your situation depend on the exact facts and timeline, which a qualified advocate can assess.

### 2. Possible relevant legal areas

Your situation may involve provisions of the Indian criminal law. Because India's criminal codes were replaced on 1 July 2024, the applicable law depends on when the events occurred. A lawyer will identify the specific statutory provisions based on your case details.

### 3. General procedural options that exist

Depending on the specifics of your situation, general procedural options that may exist include:
- Filing or responding to a complaint through appropriate legal channels
- Applying for bail (anticipatory or regular) if applicable
- Seeking mediation or counselling where available
- Filing applications or petitions in the appropriate court
- Requesting legal aid if eligible

### 4. Logical next steps you may consider

1. **Consult a qualified criminal lawyer** as soon as possible — this is the most important step.
2. **Preserve all relevant documents** and communications related to your matter.
3. **Avoid any contact** that could complicate your situation or lead to further complaints.
4. **Gather identity and residence documents** in case they are needed for legal proceedings.
5. **Note down the timeline** of events as accurately as you can — dates matter for determining which law applies.

### 5. Documents / information that often help

- Copy of the FIR or complaint (if available)
- Identity documents (Aadhaar, PAN, passport)
- Relevant communications (messages, emails, letters)
- Any documents related to the subject matter (property papers, marriage certificate, financial records, etc.)
- Proof of residence

### 6. Free legal aid

{legal_aid}

### 7. Important Disclaimer

---
*This is general educational information only and not legal advice. Every case is different. You must consult a qualified advocate before taking any step.*"""


def get_search_failure_notice() -> str:
    """Return a notice when online search fails but offline guidance proceeds."""
    return (
        "\n\n> **Note:** Online verification of current statutory provisions "
        "was unavailable at the time of this response. The guidance above is "
        "based on established general procedure. For the most current "
        "information, consult a qualified advocate or visit "
        "[India Code](https://indiacode.nic.in).\n"
    )
