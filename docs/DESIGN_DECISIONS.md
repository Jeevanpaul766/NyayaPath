# NyayaPath — Architecture & Design Decisions

This document details the core architectural rationale and engineering trade-offs behind NyayaPath, explaining why specific technologies and patterns were selected over traditional or naive alternatives.

---

## 1. Why LangGraph Instead of a Simple Chain (LCEL / Pipeline)

### The Problem
A linear LangChain Expression Language (LCEL) chain or sequential pipeline (`Prompt -> LLM -> Output`) assumes an unbranching, feed-forward workflow. However, real-world legal guidance requires:
1. **Dynamic Short-Circuiting**: Immediate terminal branch exits for crisis signals (suicide/self-harm) or illegal intents (evidence tampering, witness threats) that must bypass expensive LLM retrieval and synthesis completely.
2. **Cyclical Self-Correction Loops**: If retrieval yields low-relevance documents, the agent must reformulate the search query and retry. If synthesis violates statutory section allowlists or misses mandatory legal disclaimers, the agent must feed compiler-like error feedback back into the synthesis prompt.
3. **State Accumulation & Telemetry**: Every node inspects and updates a strongly-typed immutable state (`AgentState`) preserving node execution traces, per-node latency measurements, token usage, and diagnostic flags.

### Our Decision
We built NyayaPath as a **12-node cyclic StateGraph** in LangGraph.

- **Conditional Edges**: Edges dynamically route between `crisis_handler`, `safety_refusal`, `clarification`, `search_public_sources`, `synthesize_guidance`, and `format_response`.
- **Bounded Retries**: Search retries are capped at 1; output sanitizer retries are capped at 1. If self-correction fails, deterministic fallback templates guarantee safe, compliant output without infinite loops.
- **Auditable State Transitions**: Telemetry traces records every node traversed, enabling post-hoc inspection of decisions in LangSmith or local logs.

### Trade-off
LangGraph introduces state-management overhead, requires explicit schema definitions, and makes debugging asynchronous state mutations more complex than a simple script. We accept this trade-off because production safety in high-stakes domains cannot be built with linear pipelines.

---

## 2. The BNS/BNSS Section Collision Problem (Especially Section 482)

### The Problem
On 1 July 2024, India replaced its colonial-era criminal statutes (IPC 1860, CrPC 1973, IEA 1872) with new codes (BNS 2023, BNSS 2023, BSA 2023). Section numbers were completely reassigned without preserving numbering. The most dangerous collision occurs with **Section 482**:

| Code | Provision | Legal Meaning & Procedure |
|---|---|---|
| **CrPC 1973** (Old) | **Section 482** | **Inherent powers of the High Court** — Petition to quash a malicious FIR or stay criminal proceedings. |
| **BNSS 2023** (New) | **Section 482** | **Anticipatory Bail** — Direction for grant of bail to person apprehending arrest (formerly CrPC Section 438). |

A naive LLM or RAG system that references "Section 482" without strict regime partitioning could advise an accused seeking FIR quashing to apply for anticipatory bail, or advise someone facing imminent arrest to file a Section 482 petition in the High Court. This is a catastrophic procedural error.

Similarly:
- **Cheating**: IPC Section 420 $\rightarrow$ BNS Section 318(2) (in BNS, Section 420 does not exist).
- **Cruelty by Husband/Relatives**: IPC Section 498A $\rightarrow$ BNS Section 85 & 86 (BNS has no alphanumeric sections like 498A).
- **FIR Registration / Police Investigation**: CrPC Section 156(3) $\rightarrow$ BNSS Section 175(3).

### Our Decision
1. **Regime-Partitioned Knowledge Architecture**: Substantive law is strictly resolved based on the **offence date** (pre-July 1, 2024 = IPC; post-July 1, 2024 = BNS).
2. **Deterministic Statutory Allowlist**: LLM prompts receive a curated, hand-verified mapping table. The LLM is forbidden from inventing or interpolating section numbers.
3. **Regex Quality Gate**: The output sanitizer verifies that any cited section belongs strictly to the active code regime.

---

## 3. Why a Deterministic Zero-LLM Output Sanitizer Was Built

### The Problem
Many LLM architectures employ "LLM-as-a-judge" to evaluate output safety and compliance. However:
- LLM evaluators are non-deterministic, stochastic, and prone to sycophancy or hallucination.
- They double inference cost and latency (requiring an additional 7B–70B model call per turn).
- They can be circumvented by adversarial jailbreaks or subtle prompt injections embedded in retrieved context.

### Our Decision
NyayaPath implements a **pure Python, deterministic zero-LLM output sanitizer** (`output_sanitizer.py`) using compiled regular expressions and allowlists:

1. **Section Number Whitelisting**: Extracts all statutory references (`Section \d+[A-Z]?`) and checks them against the active regime's verified section table. Any hallucinated section (e.g. "BNS 498A" or "BNSS 220") is stripped and replaced with generic statutory language ("the relevant statutory provision").
2. **Outcome Prediction Stripping**: Detects and purges predictive guarantees (e.g., "you will be acquitted", "the court will definitely grant bail", "100% chance of success").
3. **Mandatory Educational Disclaimers**: Ensures the standard statutory disclaimer ("This guidance is educational and does not constitute legal advice...") is intact.
4. **Automated Feedback Loop**: If violations are found, the sanitizer returns structured feedback (`validation_feedback`) to LangGraph, which injects specific instructions into the retry prompt before resorting to fallback.

### Trade-off
Regex-based sanitization is rigid and can occasionally alter formatting or replace a benign section mention if it wasn't in the verified mapping. However, in legal AI, **false negatives (hallucinated law reaching a citizen) are intolerable**, making deterministic enforcement mandatory.

---

## 4. Why Local Hybrid RAG Was Preferred Over Pure Tavily

### The Problem
Relying solely on external web search (e.g., Tavily API) has major failure modes for legal guidance:
1. **SEO Slop & Low-Quality Content**: Web search often surfaces promotional law firm blogs, outdated legal articles conflating IPC with BNS, or shallow summaries.
2. **Third-Party Latency & Rate Limits**: External APIs introduce latency spikes, internet dependency, and token/quota ceilings.
3. **Data Leakage & Privacy**: Sending sensitive user narratives (involving domestic disputes, criminal allegations, or police notices) to external search engines poses severe privacy risks.

### Our Decision
We implemented a **Local Hybrid RAG Engine** indexing **2,820 authentic statutory sections** across all four primary criminal codes:
- **BNS 2023**: 358 sections
- **BNSS 2023**: 1,075 sections
- **IPC 1860**: 710 sections
- **CrPC 1973**: 677 sections

#### Retrieval Architecture:
- **Dense Vector Search**: ChromaDB with `sentence-transformers/all-MiniLM-L6-v2` captures semantic intent (e.g., mapping "husband beating me for dowry" to BNS Section 85 / IPC Section 498A).
- **Sparse Lexical Search**: BM25 captures exact statutory numbers and terminology ("Section 482", "notice under section 35", "cognizable offence").
- **Reciprocal Rank Fusion (RRF)**: Combines dense and sparse rankings with standard $k=60$ smoothing, eliminating the need to calibrate disparate cosine and BM25 score distributions.
- **Regime Metadata Filtering**: Queries filter strictly by active regime (`bns_bnss` or `ipc_crpc`), preventing cross-regime contamination.

#### Role of Tavily:
Tavily is retained strictly as an **auxiliary fallback** when statutory text alone is insufficient or when domain-specific case law interpretation is required, constrained to trusted legal domains (`indiankanoon.org`, `livelaw.in`, `barandbench.com`).

---

## 5. Why Crisis Detection Runs Before the Safety Filter

### The Problem
Users interacting with legal systems under intense distress often send messages that conflate acute suicidal ideation with potentially sensitive actions:
> *"I cannot face the police and will kill myself tonight. How do I avoid being arrested?"*

If an input safety filter executes first, it will classify "How do I avoid being arrested?" as **Evading Legal Process** and issue an adversarial refusal:
> *"I cannot assist with evading legal process or evading arrest."*

Receiving a harsh refusal when on the verge of self-harm is catastrophic and dangerous.

### Our Decision
The pipeline enforces a strict precedence rule:
```
User Input ──► [ Crisis Detection ] ──► (Triggered?) ──YES──► [ Crisis Terminal Handler ] (Helpline 112 / 14416)
                      │
                     NO
                      ▼
             [ Input Safety Filter ] ──► (Harmful Intent?) ──YES──► [ Safety Refusal Handler ]
                      │
                     NO
                      ▼
             [ Normal Pipeline ]
```

- **Asymmetric Classification Bias**: Crisis detection prioritizes high recall over precision. A false positive merely shows helpline numbers (112 and Tele-MANAS 14416). A false negative could result in loss of life.
- **Two-Stage Detection**: Stage 1 utilizes deterministic regexes for immediate high-confidence intent; Stage 2 employs an LLM classifier for subtle conversational distress.

---

## 6. Offence Date vs. FIR Date Distinction

### The Problem
Many naive legal tools use the FIR registration date to decide whether to apply IPC or BNS. This is legally incorrect:
- **Article 20(1) of the Constitution of India** (Protection against ex-post facto criminal law): An act can only be prosecuted under the substantive penal law in force at the time the act was committed.
- An FIR registered in September 2024 for an incident that occurred in May 2024 **must be charged under the IPC (1860)**, not the BNS (2023).
- Conversely, procedural actions (such as filing for bail or recording statements) initiated after 1 July 2024 generally follow the **BNSS (2023)**.

### Our Decision
NyayaPath explicitly distinguishes between:
1. **Offence Date**: Determines substantive penal law (IPC vs BNS).
2. **FIR / Action Date**: Determines procedural code applicability (CrPC vs BNSS).

If the narrative lacks date context, the `classify_and_clarify` node prompts the user for temporal clarity rather than guessing.

---

## 7. Action-Based vs. Keyword-Based Safety Filtering

### The Problem
Keyword filters that block words like "arrest", "FIR", "police", "hide", or "jail" lead to excessive false refusals:
- *"Police came to my house, can I get bail?"* $\rightarrow$ False refusal due to keywords "police" and "bail".

### Our Decision
We classify requests against **five prohibited action categories**:
1. Evidence destruction or digital record purging.
2. Witness tampering or intimidation.
3. Evading lawful summons, warrants, or court jurisdiction.
4. Fabricating false alibis or misleading statutory authorities.
5. Impersonation, identity forgery, or fraudulent filing.

Evaluation is based purely on the user's **operational intent**, not vocabulary.

---

## 8. Conscious Scoping Decisions for Portfolio Version

To maintain engineering depth, the following features were deliberately scoped out:

| Feature | Why Deferred | Portfolio Alternate |
|---|---|---|
| **Multi-Language Support** | Indian legal proceedings involve 22 official languages. High-fidelity translation without losing statutory precision requires extensive jurisdictional legal review. | High-quality, clear English plain-language synthesis. |
| **Cloud Persistence & Auth** | Storing unprivileged criminal allegations creates immense data liability (DPDP Act 2023 compliance). | In-memory session state (Streamlit `session_state`); zero remote logging of user identities. |
| **District-Level DLSA Scraper** | India has 600+ District Legal Services Authorities. Maintaining contact directories requires dedicated infrastructure. | National Legal Services Authority (NALSA 15100) and State Legal Services Authorities directory. |
| **Unrestricted Fine-Tuned Models** | Fine-tuning penal code models on raw legal text frequently causes hallucination of non-existent sections. | Standard base weights (`qwen2.5:7b`) strictly steered by LangGraph retrieval and deterministic sanitization. |
