"""
NyayaPath — Issue Category Classifier

Classifies the user's legal issue into high-level categories to
guide retrieval queries and provision lookup. Uses few-shot prompting
with the local Qwen2.5 model.
"""

from __future__ import annotations

from src.utils.logger import get_logger

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Issue Categories
# ---------------------------------------------------------------------------

ISSUE_CATEGORIES = {
    "matrimonial_cruelty": "Matrimonial disputes, dowry harassment, domestic violence (498A / BNS 85)",
    "cheating_fraud": "Cheating, fraud, dishonest inducement, breach of trust (420, 406 / BNS 318, 316)",
    "bodily_offence": "Assault, hurt, grievous hurt, criminal force (323-325, 354 / BNS 115-118, 74)",
    "criminal_intimidation": "Threats, criminal intimidation (506 / BNS 351)",
    "bail_procedure": "Bail (anticipatory, regular), arrest procedure, 41A notice",
    "fir_complaint": "FIR registration, complaint filing, magistrate complaint (154, 156(3))",
    "quashing": "Quashing of proceedings, High Court inherent powers (482 CrPC / BNSS 528)",
    "cheque_bounce": "Cheque dishonour under Section 138 NI Act",
    "general": "General legal query not fitting above categories",
}


# ---------------------------------------------------------------------------
# LLM Classifier
# ---------------------------------------------------------------------------

ISSUE_CLASSIFIER_SYSTEM_PROMPT = """You are a legal issue classifier for an Indian legal guidance system.
Classify the user's legal situation into ONE of these categories:

- matrimonial_cruelty: Dowry, domestic violence, 498A, marital cruelty
- cheating_fraud: Cheating, fraud, breach of trust, property disputes
- bodily_offence: Physical assault, hurt, grievous hurt, molestation
- criminal_intimidation: Threats, intimidation
- bail_procedure: Bail applications, arrest fears, 41A notice
- fir_complaint: Filing FIR, complaint to magistrate, police complaint
- quashing: Quashing of FIR/proceedings, High Court petition
- cheque_bounce: Cheque dishonour, bounced cheque, Section 138
- general: Does not fit any above category

Respond with EXACTLY one category name from the list above. Nothing else."""

ISSUE_CLASSIFIER_FEW_SHOT = [
    {"role": "user", "content": "My wife filed a 498A FIR against me for dowry harassment"},
    {"role": "assistant", "content": "matrimonial_cruelty"},
    {"role": "user", "content": "Someone cheated me of Rs 5 lakhs promising a job"},
    {"role": "assistant", "content": "cheating_fraud"},
    {"role": "user", "content": "I was beaten up by my neighbour and want to file a complaint"},
    {"role": "assistant", "content": "bodily_offence"},
    {"role": "user", "content": "I'm afraid of arrest, how do I get anticipatory bail?"},
    {"role": "assistant", "content": "bail_procedure"},
    {"role": "user", "content": "A cheque I received bounced, what can I do?"},
    {"role": "assistant", "content": "cheque_bounce"},
    {"role": "user", "content": "I want to get the false FIR quashed in High Court"},
    {"role": "assistant", "content": "quashing"},
]


def classify_issue(text: str, llm) -> str:
    """Classify the user's legal issue into a category.

    Args:
        text: The user's legal situation description.
        llm: A LangChain-compatible LLM instance.

    Returns:
        One of the category keys from ISSUE_CATEGORIES.
    """
    from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

    messages = [SystemMessage(content=ISSUE_CLASSIFIER_SYSTEM_PROMPT)]

    for example in ISSUE_CLASSIFIER_FEW_SHOT:
        if example["role"] == "user":
            messages.append(HumanMessage(content=example["content"]))
        else:
            messages.append(AIMessage(content=example["content"]))

    messages.append(HumanMessage(content=text))

    try:
        response = llm.invoke(messages)
        result = response.content.strip().lower()
        logger.info(f"Issue classifier result: {result}")

        # Validate against known categories
        if result in ISSUE_CATEGORIES:
            return result

        # Fuzzy match attempt
        for cat in ISSUE_CATEGORIES:
            if cat in result:
                return cat

        logger.warning(f"Unrecognized category '{result}', defaulting to 'general'")
        return "general"

    except Exception as exc:
        logger.error(f"Issue classifier LLM call failed: {exc}")
        return "general"
