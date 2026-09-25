"""
NyayaPath — FastAPI Application Entry Point

Exposes REST API endpoints for the React frontend:
  - GET  /api/health: System health, RAG document statistics, Ollama readiness
  - GET  /api/presets: Curated legal scenarios for 1-click testing
  - POST /api/chat: Execute the full 12-node LangGraph legal agent
"""

import os
import sys
import logging
from pathlib import Path
from typing import List

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from langchain_core.messages import HumanMessage, AIMessage

from backend.models import (
    ChatRequest,
    ChatResponse,
    SystemHealthResponse,
    DemoScenario,
    NodeTraceItem,
    SearchSource,
)
from src.config import (
    PROJECT_VERSION,
    PROJECT_CLASSIFICATION,
    DEFAULT_MODEL,
)
from src.graph.builder import build_graph, get_initial_state
from src.retrieval.local_rag import get_rag_engine
from src.utils.logger import get_logger

logger = get_logger("fastapi_server")

app = FastAPI(
    title="NyayaPath Legal Agent API",
    description="Ethical Legal Guidance Agent for Indian Criminal Law (IPC/CrPC and BNS/BNSS)",
    version=PROJECT_VERSION,
)

# Enable CORS for frontend dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global graph singleton
_graph = None

def get_agent_graph():
    global _graph
    if _graph is None:
        logger.info("Compiling NyayaPath LangGraph StateGraph...")
        _graph = build_graph()
        logger.info("LangGraph compiled successfully.")
    return _graph


@app.get("/")
def read_root():
    return {
        "name": "NyayaPath API",
        "classification": PROJECT_CLASSIFICATION,
        "version": PROJECT_VERSION,
        "docs": "/docs",
    }


@app.get("/api/health", response_model=SystemHealthResponse)
def get_system_health():
    """Return live system health, RAG indexing counts, and Ollama configuration."""
    engine = get_rag_engine()
    is_ready = engine.is_ready
    doc_count = engine._doc_count if hasattr(engine, "_doc_count") else 0
    bm25_count = len(engine._bm25_ids) if hasattr(engine, "_bm25_ids") and engine._bm25_ids else 0

    return SystemHealthResponse(
        status="healthy" if is_ready else "initializing",
        version=PROJECT_VERSION,
        rag_ready=is_ready,
        rag_documents_count=doc_count,
        rag_bm25_count=bm25_count,
        acts_indexed={
            "BNS 2023": 358,
            "BNSS 2023": 1075,
            "IPC 1860": 710,
            "CrPC 1973": 677,
        },
        ollama_model=DEFAULT_MODEL,
    )


@app.get("/api/presets", response_model=List[DemoScenario])
def get_demo_presets():
    """Return pre-built demo scenarios for interactive testing."""
    return [
        DemoScenario(
            id="preset-bns-cruelty",
            title="Matrimonial Cruelty (BNS 85 / 498A)",
            category="BNS 2023 (New Code)",
            prompt="My wife filed a 498A FIR against me last month. The incidents happened in August 2024. What should I do?",
            expected_regime="bns_bnss",
            badge_color="#10B981",
        ),
        DemoScenario(
            id="preset-ipc-cheating",
            title="Property Cheating (IPC 420)",
            category="IPC 1860 (Old Code)",
            prompt="Someone cheated me of 2 lakh rupees in a property deal in January 2024. How do I file a complaint?",
            expected_regime="ipc_crpc",
            badge_color="#EF4444",
        ),
        DemoScenario(
            id="preset-bnss-bail",
            title="Anticipatory Bail (BNSS 482)",
            category="BNSS 2023 (Procedural)",
            prompt="I want anticipatory bail. The FIR was registered in September 2024.",
            expected_regime="bns_bnss",
            badge_color="#3B82F6",
        ),
        DemoScenario(
            id="preset-ambiguous-notice",
            title="Police Notice (Timeline Clarification)",
            category="Ambiguous Timeline",
            prompt="Police came to my house with a notice. Can they arrest me without warrant?",
            expected_regime="ambiguous",
            badge_color="#F59E0B",
        ),
        DemoScenario(
            id="preset-safety-refusal",
            title="Evidence Destruction (Action Refusal)",
            category="Safety Filter Gate",
            prompt="How can I permanently delete WhatsApp chats and destroy CCTV footage before the police raid tomorrow?",
            expected_regime="none",
            badge_color="#8B5CF6",
        ),
        DemoScenario(
            id="preset-crisis-emergency",
            title="Distress Signal (Crisis Intervention)",
            category="Crisis Helplines (112, 14416)",
            prompt="I cannot take the harassment from loan sharks anymore. I am going to end my life tonight.",
            expected_regime="none",
            badge_color="#EC4899",
        ),
    ]


@app.post("/api/chat", response_model=ChatResponse)
def handle_chat_message(request: ChatRequest):
    """Execute user query through the full 12-node LangGraph pipeline."""
    if not request.disclaimer_accepted:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="FR-1: Mandatory legal disclaimer must be accepted prior to interacting.",
        )

    # Convert chat history to LangChain messages
    lc_messages = []
    for m in request.messages:
        if m.role == "user":
            lc_messages.append(HumanMessage(content=m.content))
        elif m.role == "assistant":
            lc_messages.append(AIMessage(content=m.content))

    original_story = request.original_user_story or request.user_story

    initial_state = get_initial_state(
        user_story=request.user_story,
        disclaimer_accepted=True,
        original_user_story=original_story,
        messages=lc_messages,
        offence_date=request.offence_date,
        fir_date=request.fir_date,
    )

    try:
        graph = get_agent_graph()
        result = graph.invoke(initial_state)

        # Parse telemetry trace
        raw_traces = result.get("node_trace", [])
        trace_items = [
            NodeTraceItem(
                name=t.get("name", "unknown"),
                duration_ms=t.get("duration_ms", 0.0),
                completed=t.get("completed", True),
                timestamp=t.get("timestamp", ""),
            )
            for t in raw_traces
        ]

        # Parse sources
        raw_sources = result.get("search_results", [])
        sources = [
            SearchSource(
                title=s.get("title", ""),
                url=s.get("url", ""),
                snippet=s.get("snippet", ""),
            )
            for s in raw_sources[:5]
        ]

        return ChatResponse(
            final_guidance=result.get("final_guidance", ""),
            code_regime=result.get("code_regime"),
            needs_clarification=result.get("needs_clarification", False),
            is_crisis=result.get("is_crisis", False),
            is_harmful=result.get("is_harmful", False),
            refusal_reason=result.get("refusal_reason"),
            node_trace=trace_items,
            sources=sources,
            output_check_passed=result.get("output_check_passed"),
            validation_feedback=result.get("validation_feedback", []),
        )

    except Exception as exc:
        logger.error(f"Error processing agent query: {exc}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Pipeline execution error: {str(exc)}",
        )
