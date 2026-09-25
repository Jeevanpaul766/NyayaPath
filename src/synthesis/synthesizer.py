"""
NyayaPath — Guidance Synthesizer

Orchestrates the LLM call to Qwen2.5 for generating the mandatory
7-part structured legal guidance response.
"""

from __future__ import annotations

from src.state import CodeRegime
from src.synthesis.prompt_templates import (
    get_synthesis_system_prompt,
    get_synthesis_user_prompt,
)
from src.utils.logger import get_logger

logger = get_logger(__name__)


def synthesize_guidance(
    user_story: str,
    issue_category: str,
    code_regime: CodeRegime,
    regime_explanation: str,
    search_results: list[dict],
    llm,
    validation_feedback: list[str] | str | None = None,
) -> str:
    """Generate the 7-part structured legal guidance.

    Args:
        user_story: The user's original legal situation description.
        issue_category: Classified issue category.
        code_regime: Determined code regime.
        regime_explanation: Human-readable regime explanation.
        search_results: Tavily search results for context.
        llm: A LangChain-compatible LLM instance.
        validation_feedback: Error/sanitizer feedback from previous attempt (for retry).

    Returns:
        The raw synthesized guidance text.
    """
    from langchain_core.messages import SystemMessage, HumanMessage

    # Build search context from results
    search_context = ""
    if search_results:
        context_parts = []
        for i, r in enumerate(search_results[:5], 1):
            content = r.get("content", "")[:500]
            url = r.get("url", "")
            title = r.get("title", "")
            if content:
                context_parts.append(f"[Source {i}: {title}]\n{content}\nURL: {url}")
        search_context = "\n\n".join(context_parts)

    system_prompt = get_synthesis_system_prompt(code_regime)
    user_prompt = get_synthesis_user_prompt(
        user_story=user_story,
        issue_category=issue_category,
        regime=code_regime,
        regime_explanation=regime_explanation,
        search_context=search_context,
    )

    # Prepend corrective feedback if this is a retry attempt
    if validation_feedback:
        if isinstance(validation_feedback, list):
            fb_text = "\n".join(f"- {f}" for f in validation_feedback if f)
        else:
            fb_text = str(validation_feedback)
        
        if fb_text.strip():
            correction_block = (
                "⚠️ CORRECTION REQUIRED FROM PREVIOUS ATTEMPT:\n"
                "The previous output failed deterministic legal validation checks for the following reasons:\n"
                f"{fb_text}\n\n"
                "CRITICAL: You MUST strictly resolve these violations. Do NOT cite prohibited sections or repeat formatting defects.\n\n"
            )
            user_prompt = correction_block + user_prompt
            logger.info("Injected validation feedback into synthesis retry prompt")

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt),
    ]

    try:
        response = llm.invoke(messages)
        guidance = response.content.strip()
        logger.info(f"Synthesis complete — {len(guidance)} chars generated")
        return guidance
    except Exception as exc:
        logger.error(f"Synthesis LLM call failed: {exc}")
        return ""
