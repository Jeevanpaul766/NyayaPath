"""
NyayaPath — LangGraph Agent State Schema

Immutable TypedDict defining the full state that flows through the
LangGraph StateGraph. Each node reads from and writes to this state.
"""

from __future__ import annotations

import operator
from typing import Annotated, Optional, Literal, Any
from typing_extensions import TypedDict
from langgraph.graph.message import add_messages


# ---------------------------------------------------------------------------
# Refusal categories — exhaustive enumeration
# ---------------------------------------------------------------------------

RefusalCategory = Literal[
    "evidence_destruction",
    "witness_intimidation",
    "evading_process",
    "false_statement_fabrication",
    "impersonation_forgery",
]

# ---------------------------------------------------------------------------
# Code regime type
# ---------------------------------------------------------------------------

CodeRegime = Literal["ipc_crpc", "bns_bnss", "ambiguous"]


# ---------------------------------------------------------------------------
# Agent State
# ---------------------------------------------------------------------------

class AgentState(TypedDict):
    """Complete state flowing through the NyayaPath LangGraph pipeline.

    The ``messages`` field uses the ``add_messages`` channel reducer so
    that each node can append messages without overwriting the history.
    All other fields are overwritten on each update.
    """

    # --- Conversation ---
    messages: Annotated[list, add_messages]

    # --- User Story ---
    user_story: str
    original_user_story: str

    # --- Date Inputs ---
    offence_date: Optional[str]
    fir_date: Optional[str]
    needs_clarification: bool

    # --- Code Regime ---
    code_regime: CodeRegime
    regime_explanation: str

    # --- Issue Classification ---
    issue_category: str

    # --- Search & Retrieval ---
    search_query: str
    search_results: list[dict[str, Any]]
    sources: list[dict[str, str]]
    evidence: list[dict[str, Any]]
    retry_count: int
    retrieval_source: str   # "local_rag" | "tavily" | "none"

    # --- Synthesis & Output ---
    raw_guidance: str
    final_guidance: str
    output_check_retries: int
    output_check_passed: bool
    validation_feedback: list[str]

    # --- Crisis Detection ---
    is_crisis: bool
    crisis_response: Optional[str]

    # --- Safety Filter ---
    is_harmful: bool
    refusal_category: Optional[RefusalCategory]
    refusal_response: Optional[str]

    # --- Session & Telemetry ---
    disclaimer_accepted: bool
    selected_model: str
    node_trace: Annotated[list[dict[str, Any]], operator.add]
