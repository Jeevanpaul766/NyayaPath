"""
NyayaPath — LangGraph Conditional Edge Functions

Routing functions that determine the next node based on current state.
These implement the branching logic in the StateGraph.
"""

from __future__ import annotations

from src.state import AgentState
from src.config import MAX_SEARCH_RETRIES, MAX_OUTPUT_CHECK_RETRIES
from src.retrieval.result_grader import grade_results
from src.utils.logger import get_logger

logger = get_logger(__name__)


def route_after_crisis(state: AgentState) -> str:
    """Route after crisis detection.

    If crisis is detected → crisis_handler_node (terminal)
    Otherwise → input_safety_filter
    """
    if state.get("is_crisis", False):
        logger.info("Routing: crisis_detection → crisis_handler")
        return "crisis_handler"
    logger.info("Routing: crisis_detection → input_safety_filter")
    return "input_safety_filter"


def route_after_safety(state: AgentState) -> str:
    """Route after safety filter.

    If harmful action detected → refusal_handler (terminal)
    Otherwise → classify_and_clarify
    """
    if state.get("is_harmful", False):
        logger.info("Routing: safety_filter → refusal_handler")
        return "refusal_handler"
    logger.info("Routing: safety_filter → classify_and_clarify")
    return "classify_and_clarify"


def route_after_classify(state: AgentState) -> str:
    """Route after classification.

    If clarification needed → clarification_node (asks user for dates)
    Otherwise → search_public_sources
    """
    if state.get("needs_clarification", False):
        logger.info("Routing: classify → clarification")
        return "clarification"
    logger.info("Routing: classify → search_public_sources")
    return "search_public_sources"


def route_after_grading(state: AgentState) -> str:
    """Route after search result grading.

    If results are low quality and retries remain → retry search
    Otherwise → synthesize_guidance
    """
    results = state.get("search_results", [])
    retry_count = state.get("retry_count", 0)

    is_acceptable, _ = grade_results(results)

    if not is_acceptable and retry_count <= MAX_SEARCH_RETRIES:
        logger.info(f"Routing: grade → search (retry {retry_count})")
        return "search_public_sources"

    logger.info("Routing: grade → synthesize_guidance")
    return "synthesize_guidance"


def route_after_output_check(state: AgentState) -> str:
    """Route after deterministic output check.

    If check failed and retries remain → re-synthesize
    Otherwise → format_final_response
    """
    passed = state.get("output_check_passed", False)
    retries = state.get("output_check_retries", 0)

    if not passed and retries <= MAX_OUTPUT_CHECK_RETRIES:
        logger.info(f"Routing: output_check → synthesize (retry {retries})")
        return "synthesize_guidance"

    logger.info("Routing: output_check → format_final_response")
    return "format_final_response"
