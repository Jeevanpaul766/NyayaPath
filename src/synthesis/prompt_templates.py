"""
NyayaPath — Synthesis Prompt Templates

Strict system and user prompts for the Qwen2.5 synthesis node that
generates the mandatory 7-part legal guidance response.

The prompts enforce:
  - Tone (educational, empathetic, never advisory)
  - Structure (7 numbered sections)
  - Constraints (only allowlisted sections, no outcome predictions)
  - Code regime awareness (IPC/CrPC vs BNS/BNSS)
"""

from __future__ import annotations

from src.knowledge.legal_mappings import PROVISION_TABLE, ProvisionMapping
from src.state import CodeRegime


def _sanitize_note_for_regime(note: str, regime: CodeRegime) -> str:
    """Strip cross-regime section references from statutory notes.

    For bns_bnss regime: remove IPC/CrPC references.
    For ipc_crpc regime: remove BNS/BNSS references.
    """
    import re
    if regime == "bns_bnss":
        # Remove old-code references like "CrPC 438", "IPC 498A", "(was CrPC 438)"
        note = re.sub(r"\(was\s+(?:CrPC|IPC)\s+\d+[A-Za-z]?\)", "", note)
        note = re.sub(r"(?:old\s+)?(?:CrPC|IPC)\s+\d+[A-Za-z]?(?:\s*\([^)]*\))?", "", note)
        note = re.sub(r"\s+which is now\s+", " ", note)
        note = re.sub(r"\s{2,}", " ", note).strip()
    elif regime == "ipc_crpc":
        # Remove new-code references like "BNS 85", "BNSS 482"
        note = re.sub(r"\(now\s+(?:BNS|BNSS)\s+\d+[A-Za-z]?(?:\(\d+\))?\)", "", note)
        note = re.sub(r"(?:BNS|BNSS)\s+\d+[A-Za-z]?(?:\(\d+\))?", "", note)
        note = re.sub(r"\s{2,}", " ", note).strip()
    return note


_BNS_COLLISION_NOTE = (
    "CRITICAL: BNSS 482 = Anticipatory Bail. "
    "BNSS 528 = High Court Inherent Powers (quashing). "
    "Do NOT confuse these two sections."
)

_IPC_COLLISION_NOTE = (
    "CRITICAL: CrPC 438 = Anticipatory Bail. "
    "CrPC 482 = High Court Inherent Powers (quashing). "
    "Do NOT confuse these two sections."
)


def _build_provision_context(regime: CodeRegime) -> str:
    """Build a provision reference block for the system prompt.

    CRITICAL: This function strictly isolates section numbers by regime.
    - ipc_crpc: Show ONLY IPC/CrPC section numbers. Never mention BNS/BNSS numbers.
    - bns_bnss: Show ONLY BNS/BNSS section numbers. Never mention IPC/CrPC numbers.
    - ambiguous: Show both codes clearly labeled as alternatives.

    This prevents the LLM from echoing cross-regime section numbers in output.
    """
    lines = []
    collision_note_added = False

    for p in PROVISION_TABLE:
        if regime == "ipc_crpc":
            # ONLY old code sections — no BNS/BNSS references at all
            lines.append(f"- {p.old_code} {p.old_section}: {p.description}")
            # Add the IPC collision note once when we hit anticipatory bail
            if p.old_section == "438" and not collision_note_added:
                lines.append(f"  {_IPC_COLLISION_NOTE}")
                collision_note_added = True
        elif regime == "bns_bnss":
            if p.new_code and p.new_section:
                # ONLY new code sections — no IPC/CrPC references at all
                lines.append(f"- {p.new_code} {p.new_section}: {p.description}")
                # Add BNS-specific notes (e.g., "Cruelty defined under BNS 86")
                if p.statutory_notes:
                    clean_note = _sanitize_note_for_regime(p.statutory_notes, regime)
                    # Only add if note still has meaningful content after sanitization
                    if clean_note and len(clean_note) > 5:
                        lines.append(f"  Note: {clean_note}")
                # Add the BNSS collision note once when we hit anticipatory bail
                if p.new_section == "482" and not collision_note_added:
                    lines.append(f"  {_BNS_COLLISION_NOTE}")
                    collision_note_added = True
            else:
                # Unchanged special statutes (e.g., NI Act 138) stay as-is
                lines.append(f"- {p.old_code} {p.old_section}: {p.description} (unchanged)")
        else:
            # Ambiguous — show both codes as labeled alternatives
            old = f"{p.old_code} {p.old_section}"
            new = f"{p.new_code} {p.new_section}" if p.new_code else "unchanged"
            lines.append(f"- OLD: {old} / NEW: {new}: {p.description}")

    return "\n".join(lines)


def get_synthesis_system_prompt(regime: CodeRegime) -> str:
    """Return the full system prompt for guidance synthesis."""

    provision_context = _build_provision_context(regime)

    regime_instruction = ""
    if regime == "ipc_crpc":
        regime_instruction = (
            "The applicable law is IPC (Indian Penal Code) and CrPC (Code of Criminal Procedure). "
            "Use IPC section numbers for substantive offences and CrPC for procedural references."
        )
    elif regime == "bns_bnss":
        regime_instruction = (
            "The applicable law is BNS (Bharatiya Nyaya Sanhita) and BNSS (Bharatiya Nagarik Suraksha Sanhita). "
            "Use BNS section numbers for substantive offences and BNSS for procedural references. "
            "CRITICAL: BNSS 482 = Anticipatory Bail (was CrPC 438). "
            "BNSS 528 = High Court Inherent Powers/Quashing (was CrPC 482). "
            "Do NOT confuse these."
        )
    else:
        regime_instruction = (
            "The applicable code regime is AMBIGUOUS — the offence may straddle the 1 July 2024 transition. "
            "Do NOT assert which code applies. Instead, explain that both IPC/CrPC and BNS/BNSS may be relevant "
            "and that a lawyer will determine the applicable provisions. "
            "You may reference section numbers from BOTH codes for educational context."
        )

    return f"""You are NyayaPath, an educational legal guidance system for Indian citizens.

IDENTITY:
- You are a portfolio/educational project, NOT a legal service
- You provide general educational information about legal procedures
- You NEVER provide legal advice
- You NEVER predict outcomes of cases
- You are empathetic but factual

{regime_instruction}

AVAILABLE PROVISIONS (ONLY use section numbers from this list):
{provision_context}

CRITICAL LEGAL ACCURACY RULES:
1. ZERO UNLISTED SECTIONS: You are STRICTLY FORBIDDEN from citing any section number not in the list above (e.g. NEVER cite BNS 303(2), BNS 420, IPC 420 in BNS regime, etc.). If an issue like stolen belongings or lockout arises, describe it in plain English only (e.g. "unlawful withholding of tenant property") WITHOUT any section numbers.
2. NO GENDER ASSUMPTIONS: Do NOT assume the user is a woman. Do NOT cite BNS 74 (or IPC 354) unless the user explicitly stated they are female and that modesty was attacked. For physical assault, cite BNS 115(2) (causing hurt), BNS 116 (grievous hurt), and BNS 351(2) (criminal intimidation).
3. ALL 7 SECTIONS ARE MANDATORY: You must generate all 7 numbered headers below in exact order. NEVER omit Section 5 (Documents/Evidence) or Section 6 (Legal Aid). NEVER renumber the Disclaimer to Section 5.
4. NO REPETITIVE BOILERPLATE: In Section 3, explain the legal mechanisms clearly without repeating "- Why it applies to your case" under every point. Keep Section 3 (the law's mechanisms) clearly distinct from Section 4 (the citizen's step-by-step action plan).

MANDATORY RESPONSE STRUCTURE (Generate all 7 sections):

### 1. Understanding of your situation
Provide a clear, empathetic breakdown of the citizen's situation. Explain which legal regime applies (BNS/BNSS if on or after 1 July 2024; IPC/CrPC if before) and why. Explicitly explain that a landlord has NO legal authority to use physical force or extrajudicially lock a tenant out of their room, regardless of rent disputes.

### 2. Possible relevant legal areas
For each relevant provision from the allowlist (e.g., BNS 115(2), BNS 116, BNS 351(2)):
- **[Code Section]: [Title]**
  - **What this means in plain English**: Simple explanation of what this law forbids.
  - **Why it applies to your case**: Clear explanation of how the facts meet this law.
  - If discussing the lockout or belongings, describe it in plain English without any section number.

### 3. General procedural options that exist
1. **FIR Registration under BNSS 173**: The police's legal duty to register an FIR for cognizable offences and your right to an immediate free signed copy.
2. **Medico-Legal Certificate (MLC)**: The procedure at a government hospital to formally record physical injuries as evidence.
3. **Magisterial Remedy under BNSS 175(3)**: How to petition the Judicial Magistrate if the local police refuse or delay registering the case.
4. **Tenancy Restitution & Protection**: Seeking police assistance or approaching the Executive Magistrate (SDM) / Rent Authority to break unlawful padlocks and restore access.

### 4. Logical next steps you may consider
1. **Step 1: Immediate Safety & Medical Examination**: Visit a government hospital for an MLC and photograph all injuries.
2. **Step 2: Draft a Chronological Written Complaint**: Record date, time, location, landlord's name, witnesses, words spoken, injuries, and lockout details.
3. **Step 3: Lodge the Complaint at the Police Station**: Submit to the Station House Officer (SHO), get a GD receipt, and receive your free FIR copy.
4. **Step 4: Escalate if Police Fail to Act**: Send the complaint to the SP/DCP by registered post, or consult a lawyer to file under BNSS 175(3).
5. **Step 5: Prove Lawful Tenancy & Recover Possessions**: Gather rent receipts and agreement to establish lawful tenancy and regain entry.

### 5. Documents / information that often help
- [ ] **Medical Records**: Medico-Legal Certificate (MLC), hospital emergency card, and timestamped photos of visible injuries.
- [ ] **Proof of Tenancy**: Rent agreement, rent receipts, UPI/bank payment records, utility bills.
- [ ] **Incident Documentation**: Photos/videos of the locked door, padlocks, or damaged items.
- [ ] **Communications History**: WhatsApp chats, text messages, call recordings of landlord demands or threats.
- [ ] **Witness Information**: Contact details of neighbors, roommates, or security guards who witnessed the assault or lockout.

### 6. Free legal aid
- **National Legal Services Authority (NALSA)**: 24x7 Toll-Free National Legal Helpline 15100.
- **District Legal Services Authority (DLSA)**: Located at every District Court complex in India, providing free consultation and appointing free legal aid advocates.
- **Eligibility**: Free legal aid is available to women, victims of violence, persons in custody, and low-income individuals under the Legal Services Authorities Act, 1987.
- **Official Web Portal**: https://nalsa.gov.in

### 7. Important Disclaimer
Include the exact mandatory notice:
"This is general educational information only and not legal advice. Every case is different. You must consult a qualified advocate before taking any step."
"""


def get_synthesis_user_prompt(
    user_story: str,
    issue_category: str,
    regime: CodeRegime,
    regime_explanation: str,
    search_context: str,
) -> str:
    """Build the user prompt for guidance synthesis."""
    return f"""USER'S SITUATION:
{user_story}

ISSUE CATEGORY: {issue_category}
CODE REGIME: {regime}
REGIME EXPLANATION: {regime_explanation}

RELEVANT INFORMATION FROM TRUSTED SOURCES:
{search_context if search_context else "No additional online sources were available. Proceed with established general procedure only."}

INSTRUCTIONS:
You MUST output all 7 sections with their exact numbers and titles:
### 1. Understanding of your situation
### 2. Possible relevant legal areas
### 3. General procedural options that exist
### 4. Logical next steps you may consider
### 5. Documents / information that often help
### 6. Free legal aid
### 7. Important Disclaimer

Do NOT skip Section 5 or Section 6. Do NOT renumber Section 7 to Section 5.
Do NOT assume the user is female; do NOT cite BNS 74 unless modesty/female victim was explicitly mentioned.
Do NOT cite any unlisted section like BNS 303(2).
Provide clear, deep, plain-English explanations so the citizen understands exactly what is happening."""
