"""
NyayaPath — Action-Based Safety Filter

Evaluates user requests against a list of **forbidden actions** (not
keywords). This is a deliberate design decision:

  Keyword-based filtering would refuse legitimate questions like
  "Can I get anticipatory bail?" because the word "bail" or "arrest"
  might trigger a false refusal. Action-based filtering evaluates the
  *intent* behind the request.

The filter classifies against five enumerated harmful action categories
and MUST NOT refuse legitimate procedural legal questions.
"""

from __future__ import annotations

from src.state import RefusalCategory
from src.utils.logger import get_logger

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Forbidden Action Categories with Examples
# ---------------------------------------------------------------------------

FORBIDDEN_ACTIONS: dict[RefusalCategory, dict] = {
    "evidence_destruction": {
        "description": "Destroying, deleting, altering, hiding, or fabricating evidence",
        "examples": [
            "How to delete WhatsApp chats before police check my phone",
            "Can I format my hard drive before the investigation",
            "How to destroy documents that prove my involvement",
            "Should I remove CCTV footage before police come",
        ],
    },
    "witness_intimidation": {
        "description": "Contacting, threatening, coaching, bribing, or pressuring witnesses or the complainant",
        "examples": [
            "How to convince my wife to withdraw the case or else",
            "Can I offer money to witnesses to change their statement",
            "How to threaten the complainant to take back the FIR",
            "Should I send someone to talk to the witnesses",
        ],
    },
    "evading_process": {
        "description": "Evading summons, arrest, absconding, fleeing jurisdiction, or hiding from police",
        "examples": [
            "How to avoid police 41A notice and leave the city",
            "Can I go underground until the case is dropped",
            "How to escape to another state to avoid arrest",
            "Should I ignore the court summons",
        ],
    },
    "false_statement_fabrication": {
        "description": "Making false statements, fabricating alibis, forging documents, or filing false counter-complaints",
        "examples": [
            "Can I create a backdated rent agreement to prove alibi",
            "How to file a false counter-complaint against her",
            "Should I make up a story for the police",
            "How to forge medical records",
        ],
    },
    "impersonation_forgery": {
        "description": "Impersonation, identity fraud, using forged documents in legal proceedings",
        "examples": [
            "Can someone appear in court on my behalf using my ID",
            "How to use a fake address proof for bail",
            "Should I use someone else's identity to avoid arrest",
        ],
    },
}


# ---------------------------------------------------------------------------
# Safety Filter System Prompt
# ---------------------------------------------------------------------------

SAFETY_FILTER_SYSTEM_PROMPT = """You are a safety evaluator for a legal guidance system. Your job is to determine if a user's request involves any FORBIDDEN ACTION.

FORBIDDEN ACTIONS (the user is asking for help with):
1. EVIDENCE_DESTRUCTION: Destroying, deleting, altering, hiding, or fabricating evidence (digital or physical)
2. WITNESS_INTIMIDATION: Contacting, threatening, coaching, bribing, or pressuring witnesses or the complainant to change/withdraw statements
3. EVADING_PROCESS: Evading summons, arrest, absconding, fleeing jurisdiction, or hiding from police/court
4. FALSE_STATEMENT_FABRICATION: Making false statements to police/court, fabricating alibis, forging documents, filing false counter-complaints
5. IMPERSONATION_FORGERY: Impersonation, identity fraud, using forged documents in legal proceedings

CRITICAL: These are LEGITIMATE legal actions and MUST NOT be refused:
- Asking about anticipatory bail, regular bail, or bail procedure
- Asking how to get a copy of an FIR
- Asking what a 41A notice requires
- Asking how to file a quashing petition
- Asking about mediation or counselling options
- Expressing fear of arrest (this is NOT evading process)
- Asking about their legal rights as an accused person
- Asking what documents they need to prepare for court
- Preserving their OWN documents and communications (this is NOT evidence tampering)

Respond in EXACTLY this format:
HARMFUL: <true or false>
CATEGORY: <EVIDENCE_DESTRUCTION|WITNESS_INTIMIDATION|EVADING_PROCESS|FALSE_STATEMENT_FABRICATION|IMPERSONATION_FORGERY|NONE>

Do not explain your reasoning."""

SAFETY_FILTER_FEW_SHOT = [
    {
        "role": "user",
        "content": "How to delete WhatsApp chats before police inspect my phone",
    },
    {"role": "assistant", "content": "HARMFUL: true\nCATEGORY: EVIDENCE_DESTRUCTION"},
    {
        "role": "user",
        "content": "Police are coming right now, they will arrest me, can I get anticipatory bail?",
    },
    {"role": "assistant", "content": "HARMFUL: false\nCATEGORY: NONE"},
    {
        "role": "user",
        "content": "How to convince my wife to withdraw the case or she will regret it",
    },
    {"role": "assistant", "content": "HARMFUL: true\nCATEGORY: WITNESS_INTIMIDATION"},
    {
        "role": "user",
        "content": "Falsely implicated in 498A, life is ruined, how do I approach High Court for quashing?",
    },
    {"role": "assistant", "content": "HARMFUL: false\nCATEGORY: NONE"},
    {
        "role": "user",
        "content": "How to avoid police 41A notice and leave the city",
    },
    {"role": "assistant", "content": "HARMFUL: true\nCATEGORY: EVADING_PROCESS"},
    {
        "role": "user",
        "content": "What documents should I keep ready for bail hearing?",
    },
    {"role": "assistant", "content": "HARMFUL: false\nCATEGORY: NONE"},
]


# ---------------------------------------------------------------------------
# Category Mapping
# ---------------------------------------------------------------------------

_CATEGORY_MAP: dict[str, RefusalCategory] = {
    "EVIDENCE_DESTRUCTION": "evidence_destruction",
    "WITNESS_INTIMIDATION": "witness_intimidation",
    "EVADING_PROCESS": "evading_process",
    "FALSE_STATEMENT_FABRICATION": "false_statement_fabrication",
    "IMPERSONATION_FORGERY": "impersonation_forgery",
}


# ---------------------------------------------------------------------------
# Refusal Response Generator
# ---------------------------------------------------------------------------

def format_refusal_response(category: RefusalCategory) -> str:
    """Generate a clear, empathetic refusal response for a harmful action request.

    The response explains WHY the request cannot be fulfilled, reminds
    the user that legitimate legal options exist, and always surfaces
    free legal aid.
    """
    action_desc = FORBIDDEN_ACTIONS[category]["description"]

    return (
        f"## I cannot help with this request\n\n"
        f"Your question appears to involve **{action_desc}**, which is "
        f"illegal and could result in additional criminal charges against you.\n\n"
        f"I am designed to provide educational information about legitimate "
        f"legal procedures only. I cannot assist with any action that involves "
        f"interfering with an investigation, court proceeding, or the rights "
        f"of other parties.\n\n"
        f"**Legitimate options you can ask about instead:**\n"
        f"- Anticipatory bail or regular bail\n"
        f"- Filing a quashing petition in the High Court\n"
        f"- Mediation and counselling options\n"
        f"- Your rights as an accused person\n"
        f"- How to find a lawyer or access free legal aid\n\n"
        f"**Free Legal Aid:** Contact NALSA helpline **15100** (toll-free) "
        f"or visit https://nalsa.gov.in\n\n"
        f"---\n"
        f"*This is general educational information only and not legal advice. "
        f"Every case is different. You must consult a qualified advocate "
        f"before taking any step.*"
    )


# ---------------------------------------------------------------------------
# LLM-Based Action Classifier
# ---------------------------------------------------------------------------

def classify_safety_with_llm(
    text: str, llm
) -> tuple[bool, RefusalCategory | None]:
    """Classify user input against forbidden action categories.

    Args:
        text: The user's message.
        llm: A LangChain-compatible LLM instance.

    Returns:
        Tuple of (is_harmful, refusal_category_or_None).
    """
    from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

    messages = [SystemMessage(content=SAFETY_FILTER_SYSTEM_PROMPT)]

    for example in SAFETY_FILTER_FEW_SHOT:
        if example["role"] == "user":
            messages.append(HumanMessage(content=example["content"]))
        else:
            messages.append(AIMessage(content=example["content"]))

    messages.append(HumanMessage(content=text))

    try:
        response = llm.invoke(messages)
        result = response.content.strip()
        logger.info(f"Safety filter result: {result}")

        # Parse structured response
        lines = result.strip().split("\n")
        is_harmful = False
        category = None

        for line in lines:
            line_upper = line.strip().upper()
            if line_upper.startswith("HARMFUL:"):
                is_harmful = "TRUE" in line_upper
            elif line_upper.startswith("CATEGORY:"):
                cat_str = line_upper.replace("CATEGORY:", "").strip()
                category = _CATEGORY_MAP.get(cat_str)

        return is_harmful, category

    except Exception as exc:
        logger.error(f"Safety filter LLM call failed: {exc}")
        # On failure, do NOT refuse (avoid over-refusal)
        return False, None


def evaluate_safety(
    text: str, llm
) -> tuple[bool, RefusalCategory | None, str | None]:
    """Full safety evaluation pipeline.

    Args:
        text: The user's message.
        llm: LangChain LLM instance.

    Returns:
        Tuple of (is_harmful, refusal_category, refusal_response).
    """
    is_harmful, category = classify_safety_with_llm(text, llm)

    if is_harmful and category:
        response = format_refusal_response(category)
        return True, category, response

    return False, None, None
