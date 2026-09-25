# NyayaPath — Reference Repository Analysis

## Purpose

Before making architectural changes to NyayaPath, we formally evaluate five
reference repositories and document which patterns to adopt, adapt, or defer.
This prevents scope creep and ensures every borrowed idea has a clear rationale.

---

## Analysis Matrix

| # | Reference | Core Idea | NyayaPath Application | Decision | Rationale |
|---|-----------|-----------|----------------------|----------|-----------|
| 1 | **Agency Agents** | Specialized agent roles with crisp contracts | Specialized LangGraph nodes with typed input/output contracts (Researcher, Grader, Synthesizer) | **ADOPT (as Node Contracts)** | Improves modularity by giving each node a clear responsibility and typed interface, without creating a multi-agent swarm. Each node already maps to one concern (crisis, safety, classify, search, grade, synthesize, sanitize). |
| 2 | **OpenMontage** | Explicit pipeline data contracts | Formal data contracts between pipeline stages (`EvidenceItem`, `SanitizationResult`, `ValidationReport`) | **ADOPT (Architecture)** | NyayaPath already passes dictionaries through state. Converting key data flows to typed dataclasses improves debugging, IDE support, and prevents silent key mismatches. |
| 3 | **Agent-Memory-OS** | Persistent associative memory with semantic indexing | Clean `SessionMemoryStore` interface (in-memory only) | **ADAPT PATTERN ONLY** | Legal queries are sensitive and must NOT persist to disk. We adopt the clean interface pattern (store/retrieve/clear) but implement only in-memory storage. The interface is swappable if a future version needs persistence with encryption. |
| 4 | **Browser Use** | Headless browser automation for web research | Future research capability | **DEFER / FUTURE** | Tavily statutory retrieval must be perfected first. Browser automation adds complexity (Playwright dependency, anti-bot handling) without solving the core domain problems. Documented as a roadmap item. |
| 5 | **Graft** | Codebase context tooling for LLM-assisted development | Developer workflow aid | **REFERENCE ONLY** | Graft is a development tool, not a runtime dependency. It informed how we structure our codebase for LLM readability (clear module boundaries, typed state, docstrings) but adds no runtime code. |

---

## Detailed Analysis

### 1. Agency Agents → Node Contracts

**What we take:**
- Each LangGraph node has a single, well-defined responsibility
- Node inputs and outputs are typed and documented
- Nodes communicate exclusively through the shared `AgentState` — no side channels

**What we do NOT take:**
- Multi-agent orchestration (LangGraph's single graph is sufficient)
- Agent-to-agent messaging (unnecessary complexity)
- Dynamic agent spawning (fixed pipeline is simpler and auditable)

**Implementation in NyayaPath:**
- `crisis_detection_node` → reads `user_story`, writes `is_crisis`, `crisis_response`
- `input_safety_filter_node` → reads `user_story`, writes `is_harmful`, `refusal_category`
- `classify_and_clarify_node` → reads `user_story`, dates; writes `code_regime`, `issue_category`
- `search_public_sources_node` → reads `issue_category`, `code_regime`; writes `search_results`
- `grade_and_retry_node` → reads `search_results`; writes `retry_count`
- `synthesize_guidance_node` → reads full context; writes `raw_guidance`
- `deterministic_output_check_node` → reads `raw_guidance`; writes `final_guidance`

---

### 2. OpenMontage → Data Contracts

**What we take:**
- Typed dataclasses for pipeline data (not raw dicts)
- Explicit validation at stage boundaries
- Single source of truth for data shapes

**Existing contracts in NyayaPath:**
- `ProvisionMapping` — hand-verified legal provision mapping (already a frozen dataclass)
- `SanitizationResult` — output sanitizer result (already a dataclass)

**New contracts to add (Module 5):**
- `EvidenceItem` — structured search result after domain validation
  - Fields: `source_id`, `title`, `url`, `domain`, `authority`, `supporting_text`, `quality_score`

---

### 3. Agent-Memory-OS → Session Memory Interface

**What we take:**
- Clean interface: `store_turn()`, `get_history()`, `get_original_story()`, `clear()`
- Separation of conversation memory from agent state

**What we explicitly reject:**
- Disk persistence (legal queries are sensitive)
- Semantic indexing (unnecessary for a 2–5 turn conversation)
- Cross-session memory (violates privacy requirements)

**Implementation:** In-memory dict keyed by Streamlit `session_id`. Cleared on session end.

---

### 4. Browser Use → Deferred

**Why defer:**
1. Tavily search already provides web results with domain filtering
2. Browser automation requires Playwright (heavy dependency)
3. Indian legal sites often have anti-bot protections
4. The core domain problems (regime handling, section collisions) don't require browser automation

**Future conditions for adoption:**
- If Tavily free tier becomes insufficient
- If specific statutory databases require JavaScript rendering
- Only after Modules 2–8 are complete and verified

---

### 5. Graft → Reference Only

**What it informed:**
- Clear module boundaries with `__init__.py` re-exports
- Typed state schema (`AgentState` TypedDict)
- Comprehensive docstrings explaining domain-specific logic
- Test files co-located with clear naming conventions

**No runtime code added.**

---

## Decision Log

| Date | Decision | Context |
|------|----------|---------|
| 2026-09-22 | ADOPT node contracts from Agency Agents | Each node already has one concern; formalizing contracts improves maintainability |
| 2026-09-22 | ADOPT data contracts from OpenMontage | `ProvisionMapping` and `SanitizationResult` already exist; extend to `EvidenceItem` |
| 2026-09-22 | ADAPT memory interface from Agent-Memory-OS | In-memory only; no persistence; clean interface for future extensibility |
| 2026-09-22 | DEFER Browser Use | Tavily first; browser automation adds complexity without solving core problems |
| 2026-09-22 | REFERENCE Graft | Development tool only; influenced code organization, not runtime |

---

*This document is updated as architectural decisions are made during implementation.*
