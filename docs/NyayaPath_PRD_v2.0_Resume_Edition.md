# Product Requirements Document (PRD)
## NyayaPath – Ethical Legal Guidance Agent  
### (Resume / Portfolio Edition)

**Version:** 2.0 (Resume Edition)  
**Date:** 18 September 2026  
**Classification:** Portfolio / Educational Project  
**Status:** Ready for Development  

**Purpose:**  
Demonstrate agentic AI engineering skills (LangGraph orchestration, safety design, domain-specific reasoning, evaluation discipline) for resume and portfolio use.  
This is a deliberately scoped-down implementation of a larger production vision (see Section 13).

**Scope Statement:**  
This is a portfolio / educational project only.  
It is not publicly deployed as a service, is not offered to the general public as a product, and does not solicit clients.  
It exists solely to demonstrate agentic AI engineering capability.

---

## 1. Executive Summary

NyayaPath is an AI agent that takes a user’s free-text account of a legal situation (as complainant or accused) and returns structured, plain-language educational guidance on general procedure.

It never provides legal advice and never generates loopholes or strategies to evade the law.

The build prioritises **depth over breadth**: a small number of things done correctly and demonstrably (safety design, a genuine India-specific technical problem, a working evaluation harness) rather than broad feature coverage. This shape is intentional for a portfolio piece.

**Non-negotiable principles:**
- Not legal advice
- Never generates loopholes or evasion strategies
- Safety defined by concrete harmful actions (not keywords)
- Crisis situations handled with priority and hard-coded resources
- Free legal aid pathways always surfaced
- All reasoning on local Ollama (Qwen2.5) + free Tavily only
- No bulk dataset downloads

---

## 2. Problem Statement

Ordinary Indian citizens facing FIRs, matrimonial complaints (including 498A), family disputes and similar situations often lack basic orientation about procedure and do not know which legal code applies after the 1 July 2024 transition to BNS / BNSS / BSA.

**Why this is a strong portfolio problem:**
- It contains a genuine, recent, non-obvious technical wrinkle (code-transition ambiguity) that a generic RAG tutorial will not have solved.
- It forces real safety-engineering decisions (action-based refusal vs keyword matching, crisis routing) rather than a token system-prompt disclaimer.
- When correctly scoped, it is finishable within a realistic portfolio timeframe.

**Note on focus:**  
The project includes accused-side scenarios (especially 498A) because this is a high-frequency real-world situation. The evaluation set is deliberately balanced with complainant-side cases so the system does not read as one-sided.

---

## 3. What “Done” Looks Like

A reviewer should be able to verify the following in approximately five minutes:

- [ ] Repository runs end-to-end from a clean clone (README contains exact steps)
- [ ] A visible LangGraph diagram or clear node list appears in the README
- [ ] Crisis detection demonstrably fires before the safety filter (one test case shown)
- [ ] At least three worked examples: one clear pre-cutoff case, one clear post-cutoff case, one refused adversarial case
- [ ] 15–20 case evaluation set, runnable with one command, pass/fail visible in terminal or short screen recording
- [ ] A “Design Decisions” section in the README (see Section 12)
- [ ] An honest “Known Limitations” section

---

## 4. Target Users (for framing the demo)

- Accused person (including 498A / matrimonial FIRs)
- Complainant
- General citizen facing family, property or minor criminal issues

---

## 5. Scope

### In Scope (v1 build)

- Free-text user story input
- Two clarifying questions when relevant: offence date and FIR date
- Hard-coded mapping table of 12–15 provisions
- Two code regimes handled cleanly: `ipc_crpc` and `bns_bnss`
- `ambiguous` regime: detected and honestly hedged (full dual-framing is out of scope)
- Live Tavily search restricted to trusted domains
- Structured 7-part guidance response
- Action-based safety refusals
- Crisis detection with hard-coded resources, running before the safety filter
- Always-on free legal aid information (NALSA / SLSA / locator)
- Local Ollama Qwen2.5:7b (14b optional toggle)
- Functional Streamlit UI

### Explicitly Out of Scope

- Multilingual support
- Voice input
- Document drafting
- Public deployment as a service
- District-level DLSA lookup
- Full dual-framing response for the ambiguous regime
- Advanced retry / resilience layers beyond one basic fallback
- Authentication, persistence beyond session, load testing

---

## 6. Critical Domain Requirements

### 6.1 Code Regime Handling

The new codes (BNS / BNSS / BSA) apply primarily on the basis of **when the offence was committed**, not solely when the FIR was registered. Procedural steps taken today are generally governed by BNSS even in older cases.

This distinction is the project’s core technical differentiator.

**Mandatory clarifying questions (when relevant):**
1. Roughly when did the events / alleged offence take place?
2. When was the FIR / complaint registered?

**Regimes stored in state:**
- `ipc_crpc` — offence clearly before 1 July 2024 → fully implemented
- `bns_bnss` — offence clearly on or after 1 July 2024 → fully implemented
- `ambiguous` — straddles the cutoff, user does not know, or continuing offence → detect and respond with a single honest paragraph explaining that both codes may be relevant; a lawyer will determine the applicable provisions. Full side-by-side dual framing is a known limitation.

### 6.2 Hard-Coded Mapping Table (12–15 provisions)

Structure:

```python
{
  "498A IPC": {
    "bns": "85",
    "note": "Cruelty defined in BNS 86",
    "verified_against": "indiacode.nic.in",
    "verified_on": "YYYY-MM-DD"
  },
  # 11–14 further entries
}
```

**Recommended set (select ~12–15):**
- Substantive: 498A, 420, 406, 323/324/325, 354, 506
- Procedural: CrPC 154 (FIR), 156(3), 41A, 438 (anticipatory bail), 482 (quashing), 436/437/439 (bail)
- Unchanged example: 138 NI Act (`"bns": null`, `"status": "unchanged"`)

Every entry must be hand-verified against India Code and date-stamped. Do not use a model to populate the table.

**Fallback rule (mandatory):**  
If the situation involves a provision not present in the table, the agent must describe the issue in plain language, name **no** section number, and state that a lawyer will identify the exact provision. This is enforced by the deterministic output check.

### 6.3 Action-Based Safety Guardrails

Refuse any request involving:
- Destroying, altering or fabricating evidence
- Contacting, pressuring, coaching or threatening witnesses or the complainant
- Evading summons, arrest or absconding
- Making false statements to police or court
- Impersonation or forged documents
- Any other illegal interference with investigation or trial

Legitimate procedural questions (anticipatory bail, quashing, etc.) must **not** be refused.

### 6.4 Crisis & Distress Handling

**Hard-coded resources only** (never model-generated):
- Emergency: 112
- Mental health: Tele-MANAS 14416  
  (Verify both numbers against current official sources before hard-coding.)

**Detection:**  
LLM classifier with an explicitly asymmetric prompt (prefer false positives) + a small keyword tripwire that bypasses classification for obvious high-risk phrases.

**Node order:** `crisis_detection` runs **before** `input_safety_filter`.

When crisis is detected the agent stops procedural guidance, acknowledges seriousness, surfaces the hard-coded resources, and encourages immediate human help.

### 6.5 Free Legal Aid (Always On)

Always surface:
- NALSA
- NALSA helpline (verify number before shipping)
- State Legal Services Authority (SLSA)
- Link to NALSA’s official locator

No district-level DLSA lookup in this version.

---

## 7. Functional Requirements

**FR-1** Disclaimer Gate — non-dismissible, handled via Streamlit `session_state`.

**FR-2** Clarification — collect offence date and FIR date when relevant.

**FR-3** Code Regime Determination — `ipc_crpc` | `bns_bnss` | `ambiguous`.

**FR-4** Retrieval — Tavily restricted to trusted domains. One retry on low-quality results; on second failure respond with general procedure only + escalated disclaimer.

**FR-5** Response Structure (Mandatory)
1. Understanding of your situation  
2. Possible relevant legal areas  
3. General procedural options  
4. Logical next steps  
5. Documents / information that often help  
6. Free legal aid information (always)  
7. Strong disclaimer

**FR-6** Deterministic Output Check (no second LLM call)
- Disclaimer string present
- Every section number mentioned is in the mapping-table allowlist, or none under fallback
- No outcome-prediction language
- On failure: strip unmatched section numbers and re-check once; if still failing, fall back to a fixed no-sections template

**FR-7** Session Memory — session-only. Refused requests may log only `refusal_category` (enumerated) + timestamp.

---

## 8. Technical Architecture

### Stack
- LangGraph (StateGraph)
- Local Ollama — Qwen2.5:7b
- Tavily Search + Extract (free tier, domain-filtered)
- Streamlit
- Hard-coded Python dictionaries for mapping table and crisis resources

### Node Order
1. `disclaimer_check` (passthrough; real gating in Streamlit)
2. `crisis_detection`
3. `input_safety_filter`
4. `classify_and_clarify`
5. `search_public_sources`
6. `grade_and_retry` (max 1 retry)
7. `synthesize_guidance`
8. `deterministic_output_check`
9. `format_final_response`

### State Schema
```python
class AgentState(TypedDict):
    messages: Annotated[list, add_messages]
    offence_date: Optional[str]
    fir_date: Optional[str]
    code_regime: Literal["ipc_crpc", "bns_bnss", "ambiguous"]
    issue_category: str
    search_results: list
    sources: list[dict]
    retry_count: int
    output_check_retries: int
    is_crisis: bool
    refusal_category: Optional[str]
    final_guidance: str
    disclaimer_accepted: bool
```

---

## 9. Evaluation (Scoped)

15–20 cases total:

| Bucket                       | Size | Purpose |
|------------------------------|------|---------|
| Legitimate guidance          | 8–10 | Mix of complainant / accused and regimes |
| Adversarial / harmful action | 5–6  | Safety refusals across action categories |
| Over-refusal                 | 3–4  | Legitimate rights questions phrased alarmingly |

**Case schema:**
```json
{
  "prompt": "...",
  "expected_path": "guidance | refusal | crisis",
  "must_contain": ["..."],
  "must_not_contain": ["..."],
  "expected_sections": ["..."] or null,
  "code_regime_hint": "..."
}
```

Automated string assertions via a single `eval.py` script (one command, prints pass/fail). Tone graded manually and noted in the README.

---

## 10. Sample Conversation (Output Format Specification)

**User:**  
I am the husband. My wife filed a 498A FIR against me last month. The incidents she is talking about happened over the last few months.

**Agent:**

**Understanding of your situation**  
You have described a 498A FIR registered recently concerning events from the last few months — after the 1 July 2024 code transition.

**Possible relevant legal areas**  
Cruelty-related provisions under BNS 85 (with BNS 86 defining cruelty), which replaced 498A IPC.

**General procedural options that exist**  
- Anticipatory bail under BNSS 482 (if applicable)  
- Regular bail after arrest  
- Petition for quashing in appropriate cases  
- Mediation / counselling options in some jurisdictions

**Logical next steps you may consider**  
1. Consult a criminal lawyer promptly.  
2. Preserve relevant documents and communications.  
3. Avoid direct contact that could lead to further complaints.  
4. Be ready with identity and residence proof if a bail application becomes necessary.

**Documents / information that often help**  
- Copy of the FIR  
- Marriage-related documents  
- Relevant communications  
- Proof of identity and residence

**Free legal aid**  
You may be entitled to free legal aid. Contact NALSA / your State Legal Services Authority, or use the official NALSA locator.

**Disclaimer**  
This is general educational information only and **not legal advice**. Every case is different. You must consult a qualified advocate before taking any step.

---

## 11. Acceptance Criteria

- [ ] Both offence date and FIR date collected when relevant
- [ ] `ipc_crpc` and `bns_bnss` regimes fully correct; `ambiguous` detected and honestly hedged
- [ ] Mapping table (12–15 provisions) hand-verified with dates
- [ ] Fallback rule for unmapped provisions enforced
- [ ] Crisis detection runs before safety filter and uses only hard-coded resources
- [ ] Free legal aid always surfaced
- [ ] Deterministic output checks pass (including strip-and-recheck)
- [ ] 15–20 case eval set runs with one command and results are visible
- [ ] Portfolio / educational classification is visible in the repository
- [ ] README contains Design Decisions and Known Limitations sections
- [ ] Project runs end-to-end from a clean clone with local Ollama + free Tavily only

---

## 12. README “Design Decisions” Section (Required Deliverable)

Cover at minimum:

1. The BNS/BNSS collision problem — why “482” means different things under the old and new codes, and how the agent avoids guessing.
2. The offence-date vs FIR-date distinction — why keying only off FIR date is incorrect.
3. Action-based vs keyword-based safety — why keyword refusal over-refuses legitimate questions (with a concrete example).
4. Crisis-before-safety-filter ordering — why this ordering matters.
5. What was deliberately cut and why (full dual-framing of ambiguous cases, DLSA lookup, multilingual support, larger provision table) framed as conscious scoping decisions.

---

## 13. Path to Full Production Vision (Not Built)

If taken beyond portfolio stage the following would be required:
- Full dual-framing response for the ambiguous regime
- Expanded mapping table (30–40 provisions)
- District-level DLSA lookup
- Stronger retry / resilience layers
- Larger evaluation set (~50 cases)
- Multilingual support
- Formal legal review of the scope statement before any public exposure

Listing these items signals awareness of the gap between a strong portfolio demonstration and a production system.

---

**End of PRD v2.0 (Resume Edition)**

This document is the single source of truth for the portfolio implementation of NyayaPath.  
