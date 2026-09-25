# How I Solved the Dangerous Section 482 Collision in a Legal AI Agent

*Designing an Ethical, Dual-Regime Legal Guidance System with LangGraph, ChromaDB, and Deterministic Quality Gates*

**Project:** [NyayaPath on GitHub](https://github.com/Jeevanpaul766/NyayaPath)

---

> **Disclaimer:** *NyayaPath is an independent engineering portfolio project designed strictly for educational and technical research purposes. It does not provide legal representation, legal advice, or guaranteed outcomes. Always consult an advocate enrolled with the State Bar Council before initiating judicial proceedings.*

---

## 1. Introduction

On July 1, 2024, India witnessed one of the most sweeping statutory transitions in modern common law history. The century-old penal codes—the Indian Penal Code of 1860 (IPC) and the Code of Criminal Procedure of 1973 (CrPC)—were superseded by the **Bharatiya Nyaya Sanhita, 2023 (BNS)** and the **Bharatiya Nagarik Suraksha Sanhita, 2023 (BNSS)**.

For ordinary citizens, this created massive procedural confusion. For an AI engineer building legal reasoning systems, it created a technical nightmare.

Most AI legal assistants fail catastrophically when laws change because large language models are trained on historical corpora dominated by the old regime. If you ask a generic LLM today about a recent FIR, it will confidently cite IPC sections that no longer apply, hallucinate section numbers, or worse—mix procedural rules from different eras.

I built **NyayaPath** as an agentic AI system to solve this exact transition challenge. NyayaPath accepts a citizen's natural-language account of a grievance, determines the governing statutory regime based on the date of offence, retrieves verified bare acts using a local Hybrid RAG index across 2,820 authentic legal sections, and outputs structured, plain-language procedural guidance.

Here is a glimpse of the production interface I designed for citizens:

![NyayaPath Landing Page](https://raw.githubusercontent.com/Jeevanpaul766/NyayaPath/main/docs/screenshots/01_landing_page.png)

*Figure 1: NyayaPath home console featuring real-time dual-regime corpus metrics, architectural highlights, and single-click scenario evaluation.*

Below is a live recorded session of the agent in action—from user inquiry to dual-regime routing, telemetry generation, and instant PDF legal memo export:

![NyayaPath Interactive Demo Walkthrough](https://raw.githubusercontent.com/Jeevanpaul766/NyayaPath/main/docs/screenshots/nyayapath_interactive_demo.webp)

*Figure 2: Live interactive session walkthrough demonstrating natural language query ingestion, multi-node agentic reasoning, and print-ready legal memorandum generation.*

---

## 2. The Core Legal Problem: The Section 482 Collision

When transitioning between CrPC (1973) and BNSS (2023), most people assume section numbers simply shifted up or down. But a few collisions are dangerous. The most critical is **Section 482**.

![The Section 482 Collision](https://raw.githubusercontent.com/Jeevanpaul766/NyayaPath/main/docs/screenshots/section_482_collision.png)

*Figure 3: Same section number, opposite meanings — CrPC 482 (FIR quashing) vs BNSS 482 (anticipatory bail).*

Consider what happens if an accused person whose FIR was registered in August 2024 asks an AI: *"I want to quash this false FIR. Can I file under Section 482?"*

- Under the old code, **CrPC 482** was the famous remedy invoked before High Courts to quash frivolous criminal proceedings.
- Under the new code, the High Court's inherent quashing power moved to **BNSS Section 528**.
- Meanwhile, **Section 482 in the BNSS is now Anticipatory Bail** (formerly CrPC 438)!

If an AI conflates these two regimes, it gives the citizen disastrous guidance: advising someone seeking pre-arrest bail to invoke inherent powers, or telling someone seeking FIR quashing to apply for bail.

This is not an isolated quirk. Familiar criminal landmarks shifted completely:

- **Matrimonial Cruelty:** Erstwhile IPC 498A became **BNS Section 85 / 86**.
- **Cheating & Fraud:** Erstwhile IPC 420 became **BNS Section 318(4)**.
- **Murder:** Erstwhile IPC 302 became **BNS Section 103**.
- **Arrest Guidelines:** *Arnesh Kumar* safeguards in CrPC 41A became **BNSS Section 35(3)**.

A generic RAG pipeline or fine-tuned model cannot be trusted to handle this collision probabilistically. It demands a deterministic, regime-aware architecture.

---

## 3. Why a Simple RAG Chain Is Not Enough

Many developers start legal projects with a standard "Naive RAG" pipeline:

![Naive RAG Pipeline](https://raw.githubusercontent.com/Jeevanpaul766/NyayaPath/main/docs/screenshots/naive_rag_pipeline.png)

*Figure 4: Linear RAG has no regime partition, no temporal gate, and no self-correction loop.*

In domain-specific legal workflows, this linear pattern fails in three ways:

1. **Semantic Drift & Query Ambiguity:** Citizens do not speak in legal jargon. A complainant might type: *"My tenant refuses to leave and threatened to break my bones."* An unassisted vector search often matches civil eviction tenancy acts instead of criminal trespass or grievous hurt under BNS.
2. **Search Contamination:** If a vector database contains both IPC and BNS, semantic similarity often pulls top chunks from *both* statutes simultaneously. The LLM then blends both regimes into a single hall of mirrors.
3. **Absence of Safety & Self-Correction:** When an LLM generates a hallucinated section (e.g., "BNS 999"), a linear chain has no feedback mechanism to catch the error, re-rank documents, or force an agentic query reformulation.

To achieve legal reliability, we need a cyclic agentic state machine with conditional routing, temporal gates, and deterministic quality enforcement.

---

## 4. Architecture Decisions

To address these challenges, I built NyayaPath around five core engineering decisions:

![NyayaPath Agentic Pipeline](https://raw.githubusercontent.com/Jeevanpaul766/NyayaPath/main/docs/screenshots/nyayapath_architecture.png)

*Figure 5: 12-node cyclic LangGraph with crisis-first safety, dual-regime routing, hybrid RAG, and deterministic sanitizer loops.*

### A. Cyclic StateGraph Orchestration via LangGraph

Instead of a straight execution line, NyayaPath runs on a 12-node cyclic LangGraph. If retrieved passages do not match the identified regime, the agent routes back to query rewriting. If the synthesized output fails validation checks, it enters a compiler-style retry loop before any user sees it.

### B. Dual-Regime Routing via Constitutional Article 20(1)

Article 20(1) of the Constitution of India provides fundamental protection against ex-post-facto laws: **a person can only be prosecuted under the substantive criminal law in force on the exact date the act was committed**.

- Incidents committed **on or before June 30, 2024** → Strictly IPC (1860).
- Incidents committed **on or after July 1, 2024** → Strictly BNS (2023).
- Missing date in citizen story → The agent suspends execution and enters an interactive clarification state requesting dates.

### C. Local Hybrid RAG Across 2,820 Bare Act Sections

NyayaPath does not depend on cloud vector services or general web crawls. I parsed, cleaned, and ingested the complete authentic legislative text of all 4 foundational statutes into an on-device index:

- **BNS (2023):** 358 sections
- **BNSS (2023):** 1,075 sections
- **IPC (1860):** 710 sections
- **CrPC (1973):** 677 sections
- **Total Local Corpus:** 2,820 sections

The retrieval engine blends dense semantic embeddings (`sentence-transformers/all-MiniLM-L6-v2`) via ChromaDB and sparse lexical matching via BM25, combined using **Reciprocal Rank Fusion (RRF)**:

$$RRF\_Score(d) = \sum_{m \in \{dense, sparse\}} \frac{1}{60 + \text{rank}_m(d)}$$

Most importantly, retrieval is metadata-partitioned by `code_regime`. When searching for a July 2024 case, IPC and CrPC documents are physically excluded from the search space, eliminating cross-regime contamination.

### D. Deterministic Zero-LLM Output Sanitizer

Never use an LLM to evaluate whether another LLM hallucinated legal citations. LLM-as-a-judge is slow, nondeterministic, and susceptible to the same confabulations as the generator.

NyayaPath implements a pure Python deterministic allowlist gate:

1. It extracts every cited statute and section using regular expressions.
2. It verifies every section against the pre-compiled set of 2,820 known sections.
3. If an invalid section or wrong regime is cited, the sanitizer injects corrective feedback and triggers an internal retry.
4. It deterministically strips speculative predictions (*"You will surely be acquitted"*) and enforces mandatory statutory notices.

### E. Asymmetric Safety: Crisis Detection First

In legal tech, a citizen expressing despair (*"I was cheated of my life savings and I don't see any reason to stay alive"*) must never receive a cold refusal message saying *"I cannot assist with unlawful or harmful topics."*

NyayaPath executes high-recall crisis screening **strictly before** the action-based safety filter. When self-harm or immediate distress is detected, it short-circuits execution directly to emergency care numbers (**112**, **Women Helpline 181**, **Tele-MANAS 14416**).

---

## 5. Key Engineering Insights

### 1. Offence Date vs. FIR Date

One of the trickiest edge cases in Indian criminal jurisprudence is the "straddling case": an offence took place in **May 2024** (IPC era), but the FIR was lodged in **August 2024** (BNSS era).

Under the saving clauses (Section 531 BNSS), substantive offences are charged under IPC, but the procedural investigation, notices, and bail are processed under BNSS. NyayaPath models this distinction directly in its state schema (`offence_date` vs `fir_date`).

### 2. Action-Based Safety Filtering

Keyword-based safety filters cripple legal AI because legal narratives inherently involve violence, murder, assault, and fraud. Blocking prompts containing the word "kill" or "forge" prevents victims from seeking guidance.

NyayaPath's safety filter targets **unlawful operational intent**, rejecting only requests that seek actionable help to:

1. Destroy or alter evidence
2. Intimidate or bribe witnesses
3. Evade lawful warrants or summons
4. Manufacture false alibis
5. Forge official documents

Victims reporting crimes pass cleanly through the filter.

---

## 6. Real-World Execution: Tracing a 498A Query

To test the system against real-world complexity, I ran a classic transition scenario through the agent:

> *"My wife filed a 498A FIR against me last month. The incidents happened in August 2024. What should I do?"*

The entire execution was instrumented with LangSmith and local telemetry. Here is the actual execution trace from the LangSmith dashboard:

![Live LangSmith Traces](https://raw.githubusercontent.com/Jeevanpaul766/NyayaPath/main/docs/screenshots/04_langsmith_traces.png)

*Figure 6: Real-time LangSmith execution trace showing the 12-node pipeline running against local Ollama Qwen2.5:7b.*

### Telemetry Breakdown

- **Total Pipeline Duration:** 55.02s (running fully on local hardware)
- **Node Steps:**
  - `disclaimer_check`: 0.00s (Deterministic verification)
  - `crisis_detection`: 3.66s (Clean bill of mental health)
  - `input_safety_filter`: 1.51s (Legitimate grievance query)
  - `classify_and_clarify`: 1.16s (Detected August 2024 → Classified as **BNS/BNSS**)
  - `search_public_sources`: 0.08s (Local Hybrid RAG filtered to BNS/BNSS)
  - `grade_and_retry`: 0.00s (Retrieved sections verified relevant)
  - `synthesize_guidance`: Synthesized structured plain-English guidance
  - `sanitize_output`: Verified BNS 85 against the allowlist gate

Here is how the telemetry is rendered inside the interactive web console:

![LangGraph Telemetry Drawer](https://raw.githubusercontent.com/Jeevanpaul766/NyayaPath/main/docs/screenshots/03_telemetry_trace.png)

*Figure 7: Inspection drawer revealing node latencies, active status, and validation feedback.*

And below is the formatted **Citizen Legal Guidance Memorandum** generated by the agent, ready to be printed or exported:

![Legal Guidance Memorandum Console](https://raw.githubusercontent.com/Jeevanpaul766/NyayaPath/main/docs/screenshots/02_legal_guidance_memo.png)

*Figure 8: Case Orientation Console displaying the structured 7-part legal memorandum with PDF/Text export toolbars.*

---

## 7. The Generated Output: An Authentic Legal Memorandum

Below is a screenshot of the official multi-page PDF memorandum generated by NyayaPath for this case:

![Official PDF Legal Guidance Memorandum](https://raw.githubusercontent.com/Jeevanpaul766/NyayaPath/main/docs/screenshots/05_pdf_memorandum_showcase.png)

*Figure 9: Authentic multi-page PDF Legal Guidance Memorandum — Document ID, statutory regime notice, procedural remedies, and helpline directory.*

**Download the full sample PDFs from the repository:**  
📄 [NyayaPath Legal Guidance Memorandum — 498A case (PDF)](https://github.com/Jeevanpaul766/NyayaPath/blob/main/docs/NyayaPath_Legal_Guidance_Memorandum_498A.pdf)  
📄 [Sample memorandum (PDF)](https://github.com/Jeevanpaul766/NyayaPath/blob/main/docs/sample_memorandum.pdf)

The memorandum follows a fixed **7-part educational structure**:

1. **Understanding of your situation** — regime classification from offence date  
2. **Possible relevant legal areas** — verified BNS / BNSS sections only  
3. **General procedural options** — notice under 35(3), anticipatory bail (BNSS 482), mediation, quashing (BNSS 528)  
4. **Logical next steps** — FIR copy, advocate, evidence, no witness contact  
5. **Documents that often help**  
6. **Free legal aid** — NALSA 15100, DLSA  
7. **Mandatory disclaimer** + emergency helpline directory  

Every cited section is checked against the deterministic allowlist of 2,820 bare-act sections before the user ever sees the output.

---

## 8. Results & What I Learned

### What Worked Well

1. **Zero Hallucination of Core Sections:** Across 140 automated tests and a 25-case evaluation benchmark, the deterministic allowlist gate achieved a 100% pass rate in eliminating hallucinated section numbers.
2. **Deterministic Partitioning Defeated Collisions:** By partitioning the ChromaDB index at query time based on date classification, the Section 482 collision was cleanly neutralized. BNSS queries never saw CrPC 482 chunks.
3. **Action-Based Safety Preserved Real Inquiries:** Complainants describing graphic assault or theft received comprehensive guidance without a single false safety refusal.

### Honest Limitations

- **Local LLM Latency:** Running Qwen2.5:7b locally via Ollama took ~50 seconds on consumer hardware for full multi-node cyclic execution. In a production cloud setting, an inference provider like Groq or vLLM would reduce latency to under 3 seconds.
- **Complex Multi-Offence Straddling:** While single-date offences are handled reliably, complex continuous offences stretching across both May 2024 and August 2024 still pose nuances that ultimately require human legal interpretation.
- **State-Specific Amendments:** India's criminal procedure allows individual states to amend select provisions (e.g., UP amendments to anticipatory bail). The current version indexes national bare acts only.

---

## 9. Conclusion

Building NyayaPath taught me that creating production-grade AI for high-stakes domains is fundamentally an **engineering and architecture challenge**, not simply a prompt engineering exercise.

When accuracy is non-negotiable:

- Replace vague prompts with structured StateGraphs.
- Replace fuzzy LLM evaluations with deterministic Python allowlists.
- Replace generic web search with partitioned, locally curated hybrid indices.

You can inspect the complete open-source codebase, architecture diagrams, and evaluation reports here:  
👉 **[GitHub Repository: NyayaPath](https://github.com/Jeevanpaul766/NyayaPath)**

---

## 💡 Key Takeaways

1. **Constitutional Rules Must Dictate AI Flow:** In criminal law, Article 20(1) dictates that date-of-offence determines substantive liability. Legal AI systems must use temporal classifiers as foundational routing gates.
2. **Partitioned RAG Beats Bigger Embeddings:** Solving the Section 482 collision was not achieved with larger context windows, but by physically partitioning the index into distinct statutory regimes.
3. **Combine LLMs with Deterministic Gates:** Let the LLM handle semantic comprehension and plain-language explanation; let deterministic regex allowlists verify factual correctness and section integrity.
4. **Crisis Before Safety:** Always evaluate user distress and self-harm before running operational safety filters to protect vulnerable citizens in crisis.
