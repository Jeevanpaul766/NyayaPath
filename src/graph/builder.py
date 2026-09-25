"""
NyayaPath — LangGraph StateGraph Builder

Assembles all nodes, edges, and conditional branches into a complete
LangGraph StateGraph and compiles it into a runnable graph.
"""

from __future__ import annotations

from langgraph.graph import StateGraph, END

from src.state import AgentState
from src.graph.nodes import (
    disclaimer_check_node,
    crisis_detection_node,
    crisis_handler_node,
    input_safety_filter_node,
    refusal_handler_node,
    classify_and_clarify_node,
    clarification_node,
    search_public_sources_node,
    grade_and_retry_node,
    synthesize_guidance_node,
    deterministic_output_check_node,
    format_final_response_node,
)
from src.graph.edges import (
    route_after_crisis,
    route_after_safety,
    route_after_classify,
    route_after_grading,
    route_after_output_check,
)
from src.utils.logger import get_logger

logger = get_logger(__name__)


def build_graph() -> StateGraph:
    """Construct and compile the NyayaPath LangGraph StateGraph.

    Node order per PRD:
        1. disclaimer_check
        2. crisis_detection
        3. input_safety_filter
        4. classify_and_clarify
        5. search_public_sources
        6. grade_and_retry
        7. synthesize_guidance
        8. deterministic_output_check
        9. format_final_response

    Returns:
        A compiled LangGraph runnable.
    """
    graph = StateGraph(AgentState)

    # --- Add Nodes ---
    graph.add_node("disclaimer_check", disclaimer_check_node)
    graph.add_node("crisis_detection", crisis_detection_node)
    graph.add_node("crisis_handler", crisis_handler_node)
    graph.add_node("input_safety_filter", input_safety_filter_node)
    graph.add_node("refusal_handler", refusal_handler_node)
    graph.add_node("classify_and_clarify", classify_and_clarify_node)
    graph.add_node("clarification", clarification_node)
    graph.add_node("search_public_sources", search_public_sources_node)
    graph.add_node("grade_and_retry", grade_and_retry_node)
    graph.add_node("synthesize_guidance", synthesize_guidance_node)
    graph.add_node("deterministic_output_check", deterministic_output_check_node)
    graph.add_node("format_final_response", format_final_response_node)

    # --- Set Entry Point ---
    graph.set_entry_point("disclaimer_check")

    # --- Add Edges ---
    # Linear: disclaimer → crisis_detection
    graph.add_edge("disclaimer_check", "crisis_detection")

    # Conditional: crisis_detection → crisis_handler OR input_safety_filter
    graph.add_conditional_edges(
        "crisis_detection",
        route_after_crisis,
        {
            "crisis_handler": "crisis_handler",
            "input_safety_filter": "input_safety_filter",
        },
    )

    # Terminal: crisis_handler → format_final_response → END
    graph.add_edge("crisis_handler", "format_final_response")

    # Conditional: input_safety_filter → refusal_handler OR classify_and_clarify
    graph.add_conditional_edges(
        "input_safety_filter",
        route_after_safety,
        {
            "refusal_handler": "refusal_handler",
            "classify_and_clarify": "classify_and_clarify",
        },
    )

    # Terminal: refusal_handler → format_final_response → END
    graph.add_edge("refusal_handler", "format_final_response")

    # Conditional: classify_and_clarify → clarification OR search
    graph.add_conditional_edges(
        "classify_and_clarify",
        route_after_classify,
        {
            "clarification": "clarification",
            "search_public_sources": "search_public_sources",
        },
    )

    # Terminal: clarification → END (waits for user input)
    graph.add_edge("clarification", END)

    # Linear: search → grade
    graph.add_edge("search_public_sources", "grade_and_retry")

    # Conditional: grade → search (retry) OR synthesize
    graph.add_conditional_edges(
        "grade_and_retry",
        route_after_grading,
        {
            "search_public_sources": "search_public_sources",
            "synthesize_guidance": "synthesize_guidance",
        },
    )

    # Linear: synthesize → output_check
    graph.add_edge("synthesize_guidance", "deterministic_output_check")

    # Conditional: output_check → synthesize (retry) OR format
    graph.add_conditional_edges(
        "deterministic_output_check",
        route_after_output_check,
        {
            "synthesize_guidance": "synthesize_guidance",
            "format_final_response": "format_final_response",
        },
    )

    # Terminal: format_final_response → END
    graph.add_edge("format_final_response", END)

    # --- Compile ---
    compiled = graph.compile()
    logger.info("NyayaPath graph compiled successfully")

    return compiled


def get_initial_state(
    user_story: str,
    disclaimer_accepted: bool = True,
    original_user_story: str = "",
    messages: list | None = None,
    offence_date: str | None = None,
    fir_date: str | None = None,
    selected_model: str = "",
) -> AgentState:
    """Create a fresh initial state for a conversation turn.

    Args:
        user_story: The user's current input message.
        disclaimer_accepted: Whether the user has accepted the disclaimer.
        original_user_story: The initial root case scenario (preserved across clarification turns).
        messages: Previous conversation messages (for multi-turn history).
        offence_date: Extracted or provided date of incident.
        fir_date: Extracted or provided date of FIR.
        selected_model: Name of the Ollama model chosen in the UI.

    Returns:
        A populated :class:`AgentState` ready for graph invocation.
    """
    from langchain_core.messages import HumanMessage

    initial_messages = list(messages) if messages else [HumanMessage(content=user_story)]

    return {
        "messages": initial_messages,
        "user_story": user_story,
        "original_user_story": original_user_story or user_story,
        "offence_date": offence_date,
        "fir_date": fir_date,
        "needs_clarification": False,
        "code_regime": "ambiguous",
        "regime_explanation": "",
        "issue_category": "",
        "search_query": "",
        "search_results": [],
        "sources": [],
        "evidence": [],
        "retry_count": 0,
        "raw_guidance": "",
        "final_guidance": "",
        "output_check_retries": 0,
        "output_check_passed": False,
        "validation_feedback": [],
        "is_crisis": False,
        "crisis_response": None,
        "is_harmful": False,
        "refusal_category": None,
        "refusal_response": None,
        "disclaimer_accepted": disclaimer_accepted,
        "selected_model": selected_model or "",
        "node_trace": [],
    }
