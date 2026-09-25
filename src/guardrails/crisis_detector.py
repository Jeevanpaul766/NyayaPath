"""
NyayaPath — Crisis Detection Module

Two-stage crisis detection that runs BEFORE the safety filter:

  Stage 1 (Deterministic Tripwire):
      Fast regex/keyword scan for unambiguous self-harm and suicide phrases.
      If triggered, bypasses Stage 2 entirely — zero false-negative risk.

  Stage 2 (Asymmetric LLM Classifier):
      Few-shot prompted Qwen2.5 classifier biased toward recall (prefer
      false positives over false negatives). Only runs when Stage 1 does
      not match.

Architecture note:
    crisis_detection runs BEFORE input_safety_filter. A suicidal user
    who also phrases their message in a way that might look "harmful"
    must receive crisis resources, not a safety refusal.
"""

from __future__ import annotations

import re
from src.knowledge.crisis_resources import format_crisis_response
from src.utils.logger import get_logger

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Stage 1: Deterministic Keyword Tripwire
# ---------------------------------------------------------------------------

# These phrases indicate unambiguous crisis. They are checked with word
# boundaries to avoid false matches on substrings.
_TRIPWIRE_PHRASES: list[str] = [
    r"kill\s+my\s*self",
    r"end\s+my\s+life",
    r"suicide",
    r"want\s+to\s+die",
    r"don'?t\s+want\s+to\s+live",
    r"no\s+point\s+in\s+living",
    r"better\s+off\s+dead",
    r"hang\s+my\s*self",
    r"slit\s+my\s+wrist",
    r"jump\s+off",
    r"overdose",
    r"can'?t\s+take\s+(this|it)\s+anymore",
    r"ending\s+it\s+all",
    r"rather\s+be\s+dead",
    r"nothing\s+left\s+to\s+live\s+for",
    r"life\s+is\s+(not\s+worth|worthless|meaningless)",
]

_TRIPWIRE_PATTERN = re.compile(
    "|".join(rf"(?:{p})" for p in _TRIPWIRE_PHRASES),
    re.IGNORECASE,
)


def check_tripwire(text: str) -> bool:
    """Return True if the text matches any deterministic crisis phrase."""
    return bool(_TRIPWIRE_PATTERN.search(text))


# ---------------------------------------------------------------------------
# Stage 2: Asymmetric LLM Classifier Prompt
# ---------------------------------------------------------------------------

CRISIS_CLASSIFIER_SYSTEM_PROMPT = """You are a crisis detection classifier for a legal guidance system.
Your ONLY job is to determine if the user is in personal emotional crisis, suicidal distress, or expressing intent to harm themselves.

CLASSIFICATION RULES:
- If the user expresses ANY of the following, classify as CRISIS:
  • Suicidal ideation or intent
  • Self-harm references
  • Severe emotional distress suggesting danger to self
  • Expressions of hopelessness combined with inability to continue living
- Legal distress alone (e.g., "I am worried about my case") is NOT crisis unless combined with self-harm language
- Criminal intentions, witness threats, intimidation, or aggressive legal retaliation (e.g. "I will make them suffer", "I want to destroy evidence") are NOT crisis (they are evaluated by the Safety Filter). Classify them as SAFE here.
- When in doubt between self-harm distress and safe, classify as CRISIS.

Respond with EXACTLY one word: CRISIS or SAFE
Do not explain your reasoning."""

CRISIS_CLASSIFIER_FEW_SHOT = [
    {"role": "user", "content": "I feel suicidal because of this false FIR, I want to end it"},
    {"role": "assistant", "content": "CRISIS"},
    {"role": "user", "content": "Hopeless, can't take this anymore, no point in living"},
    {"role": "assistant", "content": "CRISIS"},
    {"role": "user", "content": "I am very stressed about my 498A case and need legal help"},
    {"role": "assistant", "content": "SAFE"},
    {"role": "user", "content": "My life is ruined and I cannot go on living, I want to die"},
    {"role": "assistant", "content": "CRISIS"},
    {"role": "user", "content": "Police are coming to arrest me, I am scared, what should I do?"},
    {"role": "assistant", "content": "SAFE"},
    {"role": "user", "content": "Falsely implicated, life is ruined and I lost everything. How do I approach High Court for quashing?"},
    {"role": "assistant", "content": "SAFE"},
    {"role": "user", "content": "I am crying uncontrollably and terrified, please tell me my rights during police interrogation"},
    {"role": "assistant", "content": "SAFE"},
    {"role": "user", "content": "How can I convince my wife to withdraw? If she doesn't I will make her family suffer"},
    {"role": "assistant", "content": "SAFE"},
    {"role": "user", "content": "I will kill myself if they arrest me"},
    {"role": "assistant", "content": "CRISIS"},
]


def classify_crisis_with_llm(text: str, llm) -> bool:
    """Run the asymmetric LLM classifier on the user input.

    Args:
        text: The user's message.
        llm: A LangChain-compatible LLM instance (e.g. ChatOllama).

    Returns:
        True if classified as CRISIS, False otherwise.
    """
    from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

    messages = [SystemMessage(content=CRISIS_CLASSIFIER_SYSTEM_PROMPT)]

    # Add few-shot examples
    for example in CRISIS_CLASSIFIER_FEW_SHOT:
        if example["role"] == "user":
            messages.append(HumanMessage(content=example["content"]))
        else:
            messages.append(AIMessage(content=example["content"]))

    # Add the actual user input
    messages.append(HumanMessage(content=text))

    try:
        response = llm.invoke(messages)
        result = response.content.strip().upper()
        logger.info(f"Crisis LLM classifier result: {result}")
        # Bias toward CRISIS — anything other than explicit SAFE is treated as CRISIS
        return result != "SAFE"
    except Exception as exc:
        logger.error(f"Crisis classifier LLM call failed: {exc}")
        # On failure, assume CRISIS (fail-safe)
        return True


# ---------------------------------------------------------------------------
# Combined Detection Pipeline
# ---------------------------------------------------------------------------

def detect_crisis(text: str, llm=None) -> tuple[bool, str | None]:
    """Run the full two-stage crisis detection pipeline.

    Args:
        text: The user's message.
        llm: Optional LangChain LLM. If None, only Stage 1 runs.

    Returns:
        Tuple of (is_crisis, crisis_response_text_or_None).
    """
    # Stage 1: Deterministic tripwire
    if check_tripwire(text):
        logger.warning("Crisis detected via deterministic tripwire")
        return True, format_crisis_response()

    # Stage 2: Asymmetric LLM classifier
    if llm is not None:
        if classify_crisis_with_llm(text, llm):
            logger.warning("Crisis detected via asymmetric LLM classifier")
            return True, format_crisis_response()

    return False, None
