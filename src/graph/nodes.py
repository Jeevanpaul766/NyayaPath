"""
NyayaPath — LangGraph Node Handlers

Each function implements one node in the LangGraph StateGraph. Nodes
read from ``AgentState`` and return partial state updates.
"""

from __future__ import annotations

from typing import Any

from langchain_core.messages import HumanMessage, AIMessage

from src.state import AgentState
from src.guardrails.crisis_detector import detect_crisis
from src.guardrails.safety_filter import evaluate_safety
from src.reasoning.regime_classifier import (
    determine_regime,
    needs_date_clarification,
)
from src.reasoning.clarification_generator import get_clarification_prompt
from src.reasoning.issue_classifier import classify_issue
from src.retrieval.tavily_client import search_tavily
from src.retrieval.query_builder import build_search_query, build_reformulated_query
from src.retrieval.result_grader import grade_results, extract_sources, extract_evidence
from src.retrieval.local_rag import query_local_rag, get_rag_engine
from src.synthesis.synthesizer import synthesize_guidance
from src.synthesis.output_sanitizer import sanitize_output
from src.synthesis.fallback_templates import (
    get_no_sections_fallback,
    get_search_failure_notice,
)
import time

from src.knowledge.legal_aid_directory import format_legal_aid_block
from src.knowledge.crisis_resources import format_crisis_response
from src.config import (
    DISCLAIMER_TEXT,
    MAX_SEARCH_RETRIES,
    MAX_OUTPUT_CHECK_RETRIES,
    RAG_MIN_LOCAL_RESULTS,
    RAG_TOP_K,
    get_llm_model,
)
from src.utils.logger import get_logger

logger = get_logger(__name__)


def _trace(node_name: str, start_time: float) -> list[dict[str, Any]]:
    """Generate a telemetry record for node execution."""
    duration = (time.perf_counter() - start_time) * 1000.0
    return [{
        "name": node_name,
        "duration_ms": round(duration, 1),
        "completed": True,
    }]


def _get_llm(model_name: str | None = None):
    """Lazy-load the LLM with the specified model, or default."""
    from langchain_ollama import ChatOllama
    from src.config import OLLAMA_BASE_URL, LLM_TEMPERATURE

    selected = get_llm_model(model_name)
    return ChatOllama(
        base_url=OLLAMA_BASE_URL,
        model=selected,
        temperature=LLM_TEMPERATURE,
    )



# ---------------------------------------------------------------------------
# Node 1: Disclaimer Check
# ---------------------------------------------------------------------------

def disclaimer_check_node(state: AgentState) -> dict[str, Any]:
    """Passthrough node — real gating is in Streamlit session_state."""
    t0 = time.perf_counter()
    logger.info("Node: disclaimer_check")
    return {
        "disclaimer_accepted": state.get("disclaimer_accepted", False),
        "node_trace": _trace("disclaimer_check", t0),
    }


# ---------------------------------------------------------------------------
# Node 2: Crisis Detection
# ---------------------------------------------------------------------------

def crisis_detection_node(state: AgentState) -> dict[str, Any]:
    """Two-stage crisis detection — runs BEFORE safety filter."""
    t0 = time.perf_counter()
    logger.info("Node: crisis_detection")

    user_story = state.get("user_story", "")
    if not user_story:
        messages = state.get("messages", [])
        if messages:
            user_story = messages[-1].content if hasattr(messages[-1], "content") else str(messages[-1])

    llm = _get_llm(state.get("selected_model"))
    is_crisis, crisis_response = detect_crisis(user_story, llm)

    return {
        "is_crisis": is_crisis,
        "crisis_response": crisis_response,
        "node_trace": _trace("crisis_detection", t0),
    }


# ---------------------------------------------------------------------------
# Node 2a: Crisis Handler (terminal)
# ---------------------------------------------------------------------------

def crisis_handler_node(state: AgentState) -> dict[str, Any]:
    """Emit hard-coded crisis resources. Terminates normal processing."""
    t0 = time.perf_counter()
    logger.info("Node: crisis_handler (terminal)")

    crisis_response = state.get("crisis_response") or format_crisis_response()

    return {
        "final_guidance": crisis_response,
        "messages": [AIMessage(content=crisis_response)],
        "node_trace": _trace("crisis_handler", t0),
    }


# ---------------------------------------------------------------------------
# Node 3: Input Safety Filter
# ---------------------------------------------------------------------------

def input_safety_filter_node(state: AgentState) -> dict[str, Any]:
    """Action-based safety evaluation."""
    t0 = time.perf_counter()
    logger.info("Node: input_safety_filter")

    user_story = state.get("user_story", "")
    llm = _get_llm(state.get("selected_model"))
    is_harmful, category, refusal_response = evaluate_safety(user_story, llm)

    return {
        "is_harmful": is_harmful,
        "refusal_category": category,
        "refusal_response": refusal_response,
        "node_trace": _trace("input_safety_filter", t0),
    }


# ---------------------------------------------------------------------------
# Node 3a: Refusal Handler (terminal)
# ---------------------------------------------------------------------------

def refusal_handler_node(state: AgentState) -> dict[str, Any]:
    """Emit refusal response for harmful action requests."""
    t0 = time.perf_counter()
    logger.info("Node: refusal_handler (terminal)")

    refusal_response = state.get("refusal_response") or "Request refused due to safety policy."

    return {
        "final_guidance": refusal_response,
        "messages": [AIMessage(content=refusal_response)],
        "node_trace": _trace("refusal_handler", t0),
    }


# ---------------------------------------------------------------------------
# Node 4: Classify and Clarify
# ---------------------------------------------------------------------------

def classify_and_clarify_node(state: AgentState) -> dict[str, Any]:
    """Classify issue category and determine code regime.

    When dates are provided during a clarification follow-up, merges them
    with the original_user_story to preserve full legal context.
    """
    t0 = time.perf_counter()
    logger.info("Node: classify_and_clarify")

    user_story = state.get("user_story", "")
    original_story = state.get("original_user_story", "")
    offence_date = state.get("offence_date")
    fir_date = state.get("fir_date")

    # If this is a follow-up turn (original story exists and differs from
    # current user_story), merge the date info with the original context
    if original_story and original_story != user_story:
        # The current user_story might be just a date response like "January 2024"
        # Use the original story for classification but feed dates from follow-up
        classification_story = original_story
        # Try to extract dates from the follow-up message
        if not offence_date:
            offence_date = user_story  # The follow-up might be a date
    else:
        classification_story = user_story

    # Check if we need date clarification
    needs_dates = needs_date_clarification(offence_date, fir_date, classification_story)

    # Determine code regime
    code_regime, regime_explanation = determine_regime(
        offence_date, fir_date, classification_story
    )

    # Classify issue category using the full original story for context
    llm = _get_llm(state.get("selected_model"))
    issue_category = classify_issue(classification_story, llm)

    # Preserve original story if not already set
    updates: dict[str, Any] = {
        "needs_clarification": needs_dates,
        "code_regime": code_regime,
        "regime_explanation": regime_explanation,
        "issue_category": issue_category,
        "node_trace": _trace("classify_and_clarify", t0),
    }

    # Set original_user_story on first pass only
    if not original_story:
        updates["original_user_story"] = user_story

    return updates


# ---------------------------------------------------------------------------
# Node 4a: Clarification Node
# ---------------------------------------------------------------------------

def clarification_node(state: AgentState) -> dict[str, Any]:
    """Prompt the user for missing date information."""
    t0 = time.perf_counter()
    logger.info("Node: clarification (requesting dates)")

    prompt = get_clarification_prompt()
    user_story = state.get("user_story", "")

    context_note = ""
    if "bail" in user_story.lower():
        context_note = "\n\n*(Note: If you are facing imminent arrest, you may seek urgent interim protection or anticipatory bail through an advocate while clarifying dates.)*"

    full_response = (
        f"{prompt}"
        f"{context_note}\n\n"
        f"---\n\n"
        f"_{DISCLAIMER_TEXT}_\n\n"
        f"{format_legal_aid_block()}"
    )

    return {
        "final_guidance": full_response,
        "messages": [AIMessage(content=full_response)],
        "node_trace": _trace("clarification", t0),
    }


# ---------------------------------------------------------------------------
# Node 5: Search Public Sources
# ---------------------------------------------------------------------------

def search_public_sources_node(state: AgentState) -> dict[str, Any]:
    """Execute hybrid retrieval: Local RAG (primary) → Tavily (fallback).

    Primary path:
      - Query the local ChromaDB + BM25 hybrid index (regime-scoped).
      - If RAG returns >= RAG_MIN_LOCAL_RESULTS results, use them directly.

    Fallback path (Tavily):
      - Triggered when local index is empty or returns too few results.
      - On retry, query is reformulated to target authoritative sources.
    """
    t0 = time.perf_counter()
    logger.info("Node: search_public_sources")

    issue_category = state.get("issue_category", "general")
    code_regime = state.get("code_regime", "ambiguous")
    retry_count = state.get("retry_count", 0)

    # Build the text query
    if retry_count > 0:
        query = build_reformulated_query(
            original_query=state.get("search_query", ""),
            issue_category=issue_category,
            code_regime=code_regime,
            retry_reason="insufficient_trusted_results",
        )
    else:
        query = build_search_query(issue_category, code_regime, state.get("user_story", ""))

    # ── PRIMARY: Local Hybrid RAG ──────────────────────────────────────
    rag_regime = code_regime if code_regime in ("bns_bnss", "ipc_crpc") else None
    rag_engine = get_rag_engine()

    results: list[dict] = []
    retrieval_source = "none"

    if rag_engine.is_ready:
        rag_results = query_local_rag(
            query_text=query,
            top_k=RAG_TOP_K,
            regime_filter=rag_regime,
        )
        if len(rag_results) >= RAG_MIN_LOCAL_RESULTS:
            results = rag_results
            retrieval_source = "local_rag"
            logger.info(
                f"RAG primary retrieval: {len(results)} results "
                f"(regime={rag_regime}, query={query[:60]})"
            )
        else:
            logger.info(
                f"RAG returned {len(rag_results)} results (< {RAG_MIN_LOCAL_RESULTS}) "
                f"— falling back to Tavily"
            )
    else:
        logger.info("RAG index not ready — using Tavily")

    # ── FALLBACK: Tavily web search ────────────────────────────────────
    if not results:
        results = search_tavily(query)
        retrieval_source = "tavily"
        logger.info(f"Tavily fallback: {len(results)} results")

    sources = extract_sources(results)

    return {
        "search_query": query,
        "search_results": results,
        "sources": sources,
        "retrieval_source": retrieval_source,   # stored for telemetry/debugging
        "node_trace": _trace("search_public_sources", t0),
    }


# ---------------------------------------------------------------------------
# Node 6: Grade and Retry
# ---------------------------------------------------------------------------

def grade_and_retry_node(state: AgentState) -> dict[str, Any]:
    """Grade search results, extract evidence, and track retries."""
    t0 = time.perf_counter()
    logger.info("Node: grade_and_retry")

    results = state.get("search_results", [])
    retry_count = state.get("retry_count", 0)

    is_acceptable, reason = grade_results(results)
    evidence = extract_evidence(results)
    logger.info(
        f"Search grade: acceptable={is_acceptable}, reason={reason}, "
        f"evidence_items={len(evidence)}"
    )

    new_retry_count = retry_count + (0 if is_acceptable else 1)

    return {
        "retry_count": new_retry_count,
        "evidence": evidence,
        "node_trace": _trace("grade_and_retry", t0),
    }


# ---------------------------------------------------------------------------
# Node 7: Synthesize Guidance
# ---------------------------------------------------------------------------

def synthesize_guidance_node(state: AgentState) -> dict[str, Any]:
    """Generate the 7-part structured guidance using Qwen2.5.

    If this is a retry following a deterministic output check failure,
    corrective instructions from validation_feedback are passed into synthesis.
    """
    t0 = time.perf_counter()
    logger.info("Node: synthesize_guidance")

    llm = _get_llm(state.get("selected_model"))
    raw_guidance = synthesize_guidance(
        user_story=state.get("user_story", ""),
        issue_category=state.get("issue_category", "general"),
        code_regime=state.get("code_regime", "ambiguous"),
        regime_explanation=state.get("regime_explanation", ""),
        search_results=state.get("search_results", []),
        llm=llm,
        validation_feedback=state.get("validation_feedback", []),
    )

    if not raw_guidance:
        logger.warning("Synthesis returned empty — using fallback template")
        raw_guidance = get_no_sections_fallback()

    return {
        "raw_guidance": raw_guidance,
        "node_trace": _trace("synthesize_guidance", t0),
    }


# ---------------------------------------------------------------------------
# Node 8: Deterministic Output Check
# ---------------------------------------------------------------------------

def deterministic_output_check_node(state: AgentState) -> dict[str, Any]:
    """Run the zero-LLM deterministic sanitizer on synthesized output."""
    t0 = time.perf_counter()
    logger.info("Node: deterministic_output_check")

    raw_guidance = state.get("raw_guidance", "")
    code_regime = state.get("code_regime", "ambiguous")
    result = sanitize_output(raw_guidance, regime=code_regime)

    feedback: list[str] = []
    if result.checks_failed:
        logger.warning(f"Output checks failed: {result.checks_failed}")
        feedback.extend([f"Check failed: {cf}" for cf in result.checks_failed])
    if result.sections_stripped:
        logger.warning(f"Sections stripped: {result.sections_stripped}")
        feedback.append(
            f"Prohibited sections stripped due to regime mismatch ({code_regime}): "
            f"{', '.join(result.sections_stripped)}. "
            f"Do not cite sections outside the {code_regime} regime."
        )

    retries = state.get("output_check_retries", 0)
    new_retries = retries + (0 if result.passed else 1)

    return {
        "final_guidance": result.text,
        "output_check_passed": result.passed,
        "output_check_retries": new_retries,
        "validation_feedback": feedback,
        "node_trace": _trace("deterministic_output_check", t0),
    }


# ---------------------------------------------------------------------------
# Node 9: Format Final Response
# ---------------------------------------------------------------------------

def format_final_response_node(state: AgentState) -> dict[str, Any]:
    """Package the final response with sources and metadata."""
    t0 = time.perf_counter()
    logger.info("Node: format_final_response")

    guidance = state.get("final_guidance", "")
    sources = state.get("sources", [])
    search_results = state.get("search_results", [])

    # Add search failure notice if applicable
    if not search_results and not state.get("is_crisis") and not state.get("is_harmful"):
        guidance += get_search_failure_notice()

    # Add sources if available
    if sources:
        source_block = "\n\n**Sources consulted:**\n"
        for s in sources[:5]:
            source_block += f"- [{s['title']}]({s['url']})\n"
        guidance += source_block

    return {
        "final_guidance": guidance,
        "messages": [AIMessage(content=guidance)],
        "node_trace": _trace("format_final_response", t0),
    }
