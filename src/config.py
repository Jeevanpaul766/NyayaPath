"""
NyayaPath — Centralized Configuration

All application-wide constants, paths, model names, trusted domains,
and environment variable loading live here. Import from this module
rather than scattering magic strings across the codebase.
"""

import os
import datetime
from pathlib import Path
from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# Environment
# ---------------------------------------------------------------------------
load_dotenv()

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# ---------------------------------------------------------------------------
# LLM — Ollama
# ---------------------------------------------------------------------------
OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
DEFAULT_MODEL: str = os.getenv("OLLAMA_MODEL", "qwen2.5:7b")
FALLBACK_MODEL: str = os.getenv("OLLAMA_FALLBACK_MODEL", "qwen2.5:14b")

# Inference parameters
LLM_TEMPERATURE: float = 0.2       # Low temperature for deterministic legal output
LLM_MAX_TOKENS: int = 2048
LLM_REQUEST_TIMEOUT: int = 120     # seconds


def get_llm_model(requested_model: str | None = None) -> str:
    """Return the validated LLM model name, falling back to DEFAULT_MODEL."""
    if requested_model and requested_model.strip():
        return requested_model.strip()
    return DEFAULT_MODEL

# ---------------------------------------------------------------------------
# Search — Tavily
# ---------------------------------------------------------------------------
TAVILY_API_KEY: str = os.getenv("TAVILY_API_KEY", "")
TAVILY_SEARCH_DEPTH: str = "advanced"
TAVILY_MAX_RESULTS: int = 5

# Domain whitelist — only results from these domains are used
TRUSTED_DOMAINS: list[str] = [
    "indiacode.nic.in",
    "nalsa.gov.in",
    "ecourts.gov.in",
    "main.sci.gov.in",
    "egazette.gov.in",
    "prsindia.org",
]

# ---------------------------------------------------------------------------
# Local Hybrid RAG — Primary Retrieval
# ---------------------------------------------------------------------------

# Directory (relative to PROJECT_ROOT) where ChromaDB persists its index
RAG_PERSIST_DIR: str = "data/chroma_db"

# ChromaDB collection name
RAG_COLLECTION_NAME: str = "nyayapath_bare_acts"

# Sentence-Transformers embedding model (multilingual-aware, Indian-law tuned)
# "all-MiniLM-L6-v2" is fast and good quality; swap for a larger model if needed
RAG_EMBED_MODEL: str = "all-MiniLM-L6-v2"

# If local RAG returns fewer than this many results, fall back to Tavily
RAG_MIN_LOCAL_RESULTS: int = 2

# Maximum number of RAG results to pass to the synthesizer
RAG_TOP_K: int = 6

# Directory where bare act plain-text source files are placed for ingestion
RAG_SOURCE_DIR: str = "data/bare_acts"

# ---------------------------------------------------------------------------
# Legal Domain Constants
# ---------------------------------------------------------------------------
# The new criminal codes (BNS / BNSS / BSA) came into force on this date.
# Offences committed *before* this date fall under IPC / CrPC / IEA.
# Offences committed *on or after* this date fall under BNS / BNSS / BSA.
CODE_TRANSITION_DATE: datetime.date = datetime.date(2024, 7, 1)

# ---------------------------------------------------------------------------
# Retry / Resilience Limits
# ---------------------------------------------------------------------------
MAX_SEARCH_RETRIES: int = 1
MAX_OUTPUT_CHECK_RETRIES: int = 1

# ---------------------------------------------------------------------------
# Disclaimer text (canonical — used for both display and verification)
# ---------------------------------------------------------------------------
DISCLAIMER_TEXT: str = (
    "This is general educational information only and **not legal advice**. "
    "Every case is different. You must consult a qualified advocate before "
    "taking any step."
)

DISCLAIMER_CHECK_PHRASE: str = (
    "general educational information only and not legal advice"
)

# ---------------------------------------------------------------------------
# Portfolio / Educational Classification
# ---------------------------------------------------------------------------
PROJECT_CLASSIFICATION: str = "Portfolio / Educational Project"
PROJECT_VERSION: str = "2.0 (Resume Edition)"
