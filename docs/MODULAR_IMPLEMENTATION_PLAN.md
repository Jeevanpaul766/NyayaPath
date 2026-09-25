# NyayaPath — Modular Engineering & Hardening Plan

Turn NyayaPath into a genuinely working, reliable, stateful, tool-using LangGraph agent by systematically fixing existing broken flows, eliminating fake/dead UI components, enforcing strict domain security, implementing true multi-turn session memory, and achieving 100% pass on the evaluation suite.

## Core Rules & Non-Negotiables

> [!IMPORTANT]
> **No Swarms, No Database, No External Memory OS**: In strict accordance with the project rules, we preserve NyayaPath's single-graph architecture, local Ollama execution, and in-memory session state. We do NOT add external dependencies like Browser Use, Agent-Memory-OS, or multi-agent swarms.

> [!NOTE]
> Work will proceed **module by module**. Each module will be implemented, verified with automated tests, and confirmed before moving to the next.

---

## Architectural Mapping & Reference Repositories

Before modifying code, we document our architectural analysis of the 5 reference repositories in `docs/REFERENCE_REPOSITORIES.md`:

| Reference | Core Idea | NyayaPath Application | Decision | Reason |
|---|---|---|---|---|
| **Agency Agents** | Specialized agent roles with crisp contracts | Specialized LangGraph nodes (Researcher, Grader, Synthesizer) | **ADOPT (as Node Contracts)** | Improves code modularity without creating an unnecessary multi-agent swarm. |
| **OpenMontage** | Explicit pipeline contracts | Formal data contracts (`ResearchPlan`, `EvidenceItem`, `ValidationReport`) | **ADOPT (Architecture)** | Ensures type safety and clean state transitions between retrieval, grading, and synthesis. |
| **Agent-Memory-OS** | Persistent associative memory | Clean `SessionMemoryStore` interface | **ADAPT PATTERN ONLY** | Keeps sensitive legal queries strictly in session memory (no local DB persistence), but keeps interface swappable. |
| **Browser Use** | Headless browser automation | Future research agent | **DEFER / FUTURE** | Tavily statutory retrieval must be perfected first. Documented as a future roadmap item. |
| **Graft** | Codebase context tooling | Developer workflow | **REFERENCE ONLY** | Development tool only; not a runtime dependency. |

---

## Proposed Changes — Module by Module

### Module 1: Architectural Baseline & Reference Decisions
- [NEW] `docs/REFERENCE_REPOSITORIES.md`: Formalize architectural analysis of the 5 reference repos with decisions and rationale.

---

### Module 2: Synthesis Prompt Templates & Provision Context (Resolving CASE-01 & CASE-02)
- **Problem**: When `regime == "bns_bnss"`, the prompt passed `(was IPC 498A)`, causing the LLM to output `498A IPC`. When `regime == "ipc_crpc"`, it passed `(now BNS 85)`, causing the LLM to output `BNS 85`. This caused both `CASE-01` and `CASE-02` to fail evaluation.
- [MODIFY] `src/synthesis/prompt_templates.py`:
  - Strictly isolate user-facing provisions from historical metadata.
  - When in `bns_bnss` regime: Provide **only** BNS/BNSS active sections. Do NOT expose old IPC section numbers in the synthesis prompt unless specifically requested.
  - When in `ipc_crpc` regime: Provide **only** IPC/CrPC active sections. Do NOT expose modern BNS section numbers in the synthesis prompt.
  - When in `ambiguous` regime: Provide comparative mapping clearly labeled as dual options.

---

### Module 3: Regime-Specific Allowlist & Output Sanitizer (Resolving Cross-Regime Leaks)
- **Problem**: `output_sanitizer.py` uses `get_allowlist_sections()`, which returns all 15 provisions across both regimes. If an LLM hallucinates an IPC section in a BNS case, it passes.
- [MODIFY] `src/knowledge/legal_mappings.py`:
  - Add `get_allowlist_for_regime(regime: str) -> set[str]`.
  - Returns only active IPC/CrPC sections for `ipc_crpc`, only BNS/BNSS sections for `bns_bnss`, and full set for `ambiguous`.
- [MODIFY] `src/synthesis/output_sanitizer.py`:
  - Update `sanitize_output(text, regime)` to enforce regime-specific allowlists.
  - Strip cross-regime section leaks cleanly.
- [MODIFY] `tests/test_sanitizer.py`:
  - Add unit tests verifying that IPC sections are rejected in BNS regime and vice versa.

---

### Module 4: Structured Date Extraction & Deterministic Regime Classifier (Resolving CASE-03)
- **Problem**: `determine_regime` uses a rigid regex requiring words like `incident|offence|happened` before the date. A natural sentence like *"Someone cheated me of Rs 5 lakhs in January 2024"* fails date parsing and triggers an unnecessary clarification loop.
- [MODIFY] `src/reasoning/regime_classifier.py`:
  - Enhance date parsing to recognize `"in <Month> <Year>"`, `"on <DD/MM/YYYY>"`, `"<Month> <Year>"`, and relative time expressions directly across the text without requiring action prefix keywords.
  - Implement two-stage extraction: LLM structured extraction helper for tricky natural phrasing, followed by strict deterministic evaluation against `CODE_TRANSITION_DATE` (2024-07-01).
- [MODIFY] `tests/test_regime_reasoning.py`:
  - Add unit tests for natural phrasing patterns (e.g., *"cheated me in January 2024"*, *"FIR registered last month"*, etc.).

---

### Module 5: Strict Trusted Domain Enforcement & Structured Evidence Object
- **Problem**: `result_grader.py` bypasses domain whitelisting (`elif relevance_hits >= 3`), allowing commercial blogs and Scribd documents into the sources block.
- [MODIFY] `src/retrieval/tavily_client.py`:
  - Implement strict domain normalization (strip www, check exact domain and trusted subdomains).
- [MODIFY] `src/retrieval/result_grader.py`:
  - **AUTHORIZED DOMAIN FIRST, RELEVANCE SECOND**: Immediately reject any result whose domain is not in `TRUSTED_DOMAINS`.
  - Normalize accepted results into a structured `EvidenceItem` dataclass (`source_id`, `title`, `url`, `domain`, `authority`, `supporting_text`, `quality_score`).
- [MODIFY] `src/state.py`:
  - Add `evidence: list[dict]` to `AgentState`.
- [NEW] `tests/test_retrieval_validation.py`:
  - Add unit tests proving commercial sites and unauthorized domains are rejected regardless of keyword score.

---

### Module 6: Multi-Turn Conversation Memory & Clarification State Preservation
- **Problem**: `app.py` passes only `[HumanMessage(content=prompt_to_process)]` into LangGraph. Prior turns are discarded. When replying to clarification, the original legal situation is lost.
- [MODIFY] `src/state.py`:
  - Ensure `AgentState` preserves `conversation_history`, `original_user_story`, and clarification context.
- [MODIFY] `src/graph/nodes.py`:
  - In `classify_and_clarify_node`, if dates are supplied during a follow-up, merge them with `original_user_story` to retain full context.
- [MODIFY] `app.py`:
  - Feed previous session messages into `initial_state["messages"]`.
  - Handle both direct chat inputs and date input widgets without losing the root case story.

---

### Module 7: Search & Synthesis Retries with Reformulation and Feedback
- **Problem**: Search retry repeats the identical query. Synthesis retry repeats the identical prompt with no error feedback.
- [MODIFY] `src/retrieval/query_builder.py`:
  - Implement `build_reformulated_query(original_query, issue_category, regime, retry_reason)` to target specific statutory sections (e.g. adding `site:indiacode.nic.in`).
- [MODIFY] `src/synthesis/synthesizer.py`:
  - Accept `validation_feedback` (e.g. list of prohibited sections found or missing disclaimer) and prepend corrective instructions to the prompt on retry.
- [MODIFY] `src/graph/nodes.py` & `src/graph/edges.py`:
  - Pass structured feedback into retry loops. Limit retries to 1 to prevent infinite loops.

---

### Module 8: Real Pipeline Tracing, Model Selector & UI Truthfulness
- **Problem**: `st.session_state.node_trace` is never populated. `model_selector` in the sidebar is completely ignored by `_get_llm()`.
- [MODIFY] `src/config.py`:
  - Add helper `get_llm_model(requested_model: str | None) -> str`.
- [MODIFY] `src/graph/nodes.py`:
  - Update `_get_llm(model_name: str | None = None)` to use the model selected in session state.
  - Implement execution telemetery: each node logs its execution start time, duration, and completion status into `AgentState["node_trace"]`.
- [MODIFY] `src/ui/sidebar.py` & `app.py`:
  - Display actual execution telemetry in the sidebar (Node name, status, duration in ms).
  - Add execution metrics summary: Total latency, sources accepted/rejected, model used, output validation status.
  - Add a **Demo Mode** selector (Pre-2024 case, Post-2024 case, Adversarial, Crisis).

---

### Module 9: Evaluation Suite Expansion (25 Cases) & Comprehensive Summary
- **Problem**: Need to verify all fixed capabilities (regime handling, strict domain filtering, over-refusal protection, multi-turn clarification) across a full test suite.
- [MODIFY] `eval/cases.json`:
  - Expand from 18 to 25 cases, organized into 7 explicit buckets:
    1. Legitimate Guidance (Pre-July 2024 & Post-July 2024)
    2. Harmful / Adversarial Refusals
    3. Crisis Intervention
    4. Over-refusal Protection (Panic & Emotional Queries)
    5. Regime Boundary & Continuing Offences
    6. Retrieval & Source Validation
    7. Output Sanitization & Collision Protection
- [MODIFY] `eval.py`:
  - Add category breakdown summary table (e.g. `Regime: 5/5`, `Safety: 5/5`, `Crisis: 2/2`, `Over-refusal: 2/2`).
  - Add `--category` filter flag for fast developer feedback.
- [MODIFY] `README.md`, `docs/ARCHITECTURE.md`, `docs/KNOWN_LIMITATIONS.md`:
  - Update documentation to accurately describe the completed architecture, state flow, Mermaid diagram, and design decisions.

---

## Verification Plan

### Automated Tests
1. **Unit Tests**:
   ```bash
   venv/bin/pytest -v
   ```
   Must pass all existing 88 tests plus new tests for regime allowlist, date extraction, and domain whitelist.
2. **Targeted Eval Cases**:
   ```bash
   venv/bin/python eval.py --case CASE-01
   venv/bin/python eval.py --case CASE-02
   venv/bin/python eval.py --case CASE-03
   ```
   Must all transition to `✅ PASS`.
3. **Category Eval Runs**:
   ```bash
   venv/bin/python eval.py --category regime
   venv/bin/python eval.py --category safety
   venv/bin/python eval.py --category crisis
   ```
4. **Full 25-Case Eval Harness**:
   ```bash
   venv/bin/python eval.py
   ```
   Print full summary table with genuine category pass rates.

### Manual / UI Verification
1. Run Streamlit:
   ```bash
   venv/bin/streamlit run app.py
   ```
2. Test Demo Mode presets in UI.
3. Verify that the **Pipeline Trace** updates in real-time with genuine durations in milliseconds.
4. Verify that changing the **Ollama Model** selector actually changes the model indicated in trace telemetry.
5. Verify multi-turn clarification: submit a query without dates, receive clarification, reply with dates in the main chat box, and verify that the original legal problem is correctly preserved.
