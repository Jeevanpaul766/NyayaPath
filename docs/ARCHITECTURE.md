# NyayaPath — Technical Architecture

## System Overview

NyayaPath is built as a LangGraph StateGraph with 12 nodes, 5 conditional edge functions, and 2 retry loops. The architecture follows a strict pipeline design where each node reads from and writes to a shared `AgentState` TypedDict.

## Design Principles

1. **Safety First**: Crisis detection runs before safety filtering. A distressed user always receives help.
2. **Deterministic Quality Gates**: The output sanitizer uses zero LLM calls — only regex and string matching.
3. **No Hallucinated Sections**: The LLM can only reference section numbers from the hand-verified mapping table.
4. **Graceful Degradation**: If search fails, the system falls back to offline general procedure. If synthesis fails, a guaranteed-compliant template is used.
5. **Single Source of Truth**: All legal provision data lives in `legal_mappings.py`. No duplicated section numbers.

## State Flow

```
AgentState (TypedDict)
├── messages (Annotated[list, add_messages])  — conversation history
├── user_story (str)                          — current user message
├── original_user_story (str)                 — root scenario preserved across clarification turns
├── offence_date / fir_date (Optional[str])   — parsed temporal data
├── needs_clarification (bool)                — whether dates are required
├── code_regime (Literal)                     — ipc_crpc | bns_bnss | ambiguous
├── regime_explanation (str)                  — explanation of governing statutory era
├── issue_category (str)                      — classified legal issue type
├── search_query (str)                        — active or reformulated Tavily query
├── search_results / sources (list)           — Tavily retrieval data
├── evidence (list[dict])                     — structured, domain-verified evidence items
├── retry_count (int)                         — search retry counter (max 1)
├── raw_guidance / final_guidance (str)        — synthesis output
├── output_check_retries (int)                — sanitizer retry counter (max 1)
├── output_check_passed (bool)                — sanitizer compliance status
├── validation_feedback (list[str])           — corrective feedback passed into synthesis retry
├── is_crisis / is_harmful (bool)             — guardrail flags
├── crisis_response / refusal_response (str)  — formatted intervention text
├── refusal_category (Optional[Literal])      — enumerated refusal type
├── disclaimer_accepted (bool)                — session gate flag
├── selected_model (str)                      — active Ollama model chosen in UI
└── node_trace (Annotated[list, operator.add])— execution step durations (ms) & statuses
```

## Node Execution Order

| # | Node | Purpose | Terminal? | Telemetry |
|---|---|---|---|---|
| 1 | `disclaimer_check` | Validates user consent | No | Logged |
| 2 | `crisis_detection` | Two-stage crisis classifier | No | Logged |
| 2a | `crisis_handler` | Emits hard-coded helplines | **Yes** | Logged |
| 3 | `input_safety_filter` | Action-based harm evaluation | No | Logged |
| 3a | `refusal_handler` | Formats refusal + alternatives | **Yes** | Logged |
| 4 | `classify_and_clarify` | Issue + regime classification + follow-up merging | No | Logged |
| 4a | `clarification` | Requests missing dates | **Yes** | Logged |
| 5 | `search_public_sources` | Domain-restricted Tavily search (with reformulation on retry) | No | Logged |
| 6 | `grade_and_retry` | Search quality evaluation & evidence extraction | No | Logged |
| 7 | `synthesize_guidance` | 7-part structured generation (with feedback on retry) | No | Logged |
| 8 | `deterministic_output_check` | Allowlist + disclaimer enforcement & feedback generation | No | Logged |
| 9 | `format_final_response` | Final packaging + sources consulted | **Yes** | Logged |

## Key Architectural Decisions

### Why LangGraph over LangChain Chains?
- Conditional branching (crisis → terminal, safety → terminal, clarify → terminal)
- Resilient retry loops with feedback:
  - Search retry reformulates query targeting `indiacode.nic.in` bare acts
  - Synthesis retry injects deterministic validation errors into prompts
- Explicit state management with typed schema and operator reducers
- Real-time pipeline execution telemetry (per-node latency tracking)

### Why Local Ollama?
- No API costs for portfolio demonstration
- Dynamic model selection (`qwen2.5:7b`, `qwen2.5:14b`, `qwen2.5:32b`) wired directly through state
- Reproducible results for evaluation harness

### Why Deterministic Output Sanitizer?
- Zero-LLM deterministic quality gate (regex and statutory allowlist)
- Prevents cross-regime hallucination (e.g. IPC Section 498A cited in BNS regime)
- Extracts structured `validation_feedback` for closed-loop self-correction
- Guaranteed safe fallback templates if retries fail
