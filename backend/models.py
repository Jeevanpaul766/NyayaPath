"""
NyayaPath — Pydantic Schemas for FastAPI Backend
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    role: str = Field(..., description="'user' or 'assistant'")
    content: str = Field(..., description="Message text")


class ChatRequest(BaseModel):
    user_story: str = Field(..., description="User's natural language legal narrative or question")
    disclaimer_accepted: bool = Field(True, description="FR-1 Disclaimer gate acceptance")
    offence_date: Optional[str] = Field(None, description="Optional clarified date of offence")
    fir_date: Optional[str] = Field(None, description="Optional clarified date of FIR/complaint")
    original_user_story: Optional[str] = Field(None, description="Preserved root story for multi-turn clarification")
    messages: List[ChatMessage] = Field(default_factory=list, description="Conversation history")


class NodeTraceItem(BaseModel):
    name: str
    duration_ms: float
    completed: bool
    timestamp: str


class SearchSource(BaseModel):
    title: str
    url: str
    snippet: Optional[str] = None


class ChatResponse(BaseModel):
    final_guidance: str
    code_regime: Optional[str] = None
    needs_clarification: bool = False
    is_crisis: bool = False
    is_harmful: bool = False
    refusal_reason: Optional[str] = None
    node_trace: List[NodeTraceItem] = Field(default_factory=list)
    sources: List[SearchSource] = Field(default_factory=list)
    output_check_passed: Optional[bool] = None
    validation_feedback: List[str] = Field(default_factory=list)


class SystemHealthResponse(BaseModel):
    status: str
    version: str
    rag_ready: bool
    rag_documents_count: int
    rag_bm25_count: int
    acts_indexed: Dict[str, int]
    ollama_model: str


class DemoScenario(BaseModel):
    id: str
    title: str
    category: str
    prompt: str
    expected_regime: str
    badge_color: str
