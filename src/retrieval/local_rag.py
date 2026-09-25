"""
NyayaPath — Local Hybrid RAG Engine

Implements a two-path retrieval system:
  1. Dense vector search via ChromaDB (sentence-transformers embeddings)
  2. Sparse lexical search via BM25 (rank-bm25)
  3. Reciprocal Rank Fusion (RRF) to merge ranked results

This is the PRIMARY retrieval path. Tavily is used only as a fallback
when the local index returns fewer than RAG_MIN_LOCAL_RESULTS results.

Index layout (ChromaDB collection "nyayapath_bare_acts"):
  document  — section text
  metadata  — {act, section_number, section_title, regime, source_file}

Usage:
    from src.retrieval.local_rag import query_local_rag
    results = query_local_rag("bail conditions under BNS", top_k=5)
"""

from __future__ import annotations

import pickle
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from src.config import PROJECT_ROOT, RAG_COLLECTION_NAME, RAG_PERSIST_DIR, RAG_EMBED_MODEL
from src.utils.logger import get_logger

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Data types
# ---------------------------------------------------------------------------

@dataclass
class RAGResult:
    """A single retrieved passage with provenance metadata."""
    text: str
    act: str
    section_number: str
    section_title: str
    regime: str
    source_file: str
    rrf_score: float = 0.0
    dense_rank: int | None = None
    sparse_rank: int | None = None

    def to_tavily_compatible(self) -> dict[str, Any]:
        """Return a dict mirroring a Tavily result so downstream code needs no changes."""
        citation = f"{self.act} § {self.section_number}"
        if self.section_title:
            citation += f" ({self.section_title})"
        return {
            "title": citation,
            "url": f"local://{self.act}/{self.section_number}",
            "content": self.text,
            "score": self.rrf_score,
            "act": self.act,
            "section": self.section_number,
            "regime": self.regime,
            "source": "local_rag",
        }


# ---------------------------------------------------------------------------
# RRF helper
# ---------------------------------------------------------------------------

def _rrf_score(rank: int, k: int = 60) -> float:
    return 1.0 / (k + rank)


def _reciprocal_rank_fusion(
    dense_ids: list[str],
    sparse_ids: list[str],
    k: int = 60,
) -> list[tuple[str, float]]:
    scores: dict[str, float] = {}
    for rank, doc_id in enumerate(dense_ids, start=1):
        scores[doc_id] = scores.get(doc_id, 0.0) + _rrf_score(rank, k)
    for rank, doc_id in enumerate(sparse_ids, start=1):
        scores[doc_id] = scores.get(doc_id, 0.0) + _rrf_score(rank, k)
    return sorted(scores.items(), key=lambda x: x[1], reverse=True)


# ---------------------------------------------------------------------------
# HybridRAGEngine — thread-safe singleton
# ---------------------------------------------------------------------------

class HybridRAGEngine:
    """Thread-safe singleton wrapping ChromaDB + BM25 retrieval."""

    _instance: HybridRAGEngine | None = None
    _lock: threading.Lock = threading.Lock()

    def __new__(cls) -> HybridRAGEngine:
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
        return cls._instance

    def _ensure_initialized(self) -> None:
        if self._initialized:
            return
        with self._lock:
            if self._initialized:
                return
            logger.info("Initialising HybridRAGEngine …")
            self._load_chromadb()
            self._load_bm25()
            self._initialized = True
            logger.info(f"HybridRAGEngine ready — {self._doc_count} sections indexed")

    def _load_chromadb(self) -> None:
        try:
            import chromadb
            from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction
        except ImportError as exc:
            raise ImportError(
                "chromadb and sentence-transformers are required. "
                "Run: pip install chromadb sentence-transformers"
            ) from exc

        persist_path = str(PROJECT_ROOT / RAG_PERSIST_DIR)
        self._chroma_client = chromadb.PersistentClient(path=persist_path)
        embed_fn = SentenceTransformerEmbeddingFunction(
            model_name=RAG_EMBED_MODEL,
            device="cpu",
        )
        self._collection = self._chroma_client.get_or_create_collection(
            name=RAG_COLLECTION_NAME,
            embedding_function=embed_fn,
            metadata={"hnsw:space": "cosine"},
        )
        self._doc_count = self._collection.count()
        logger.info(f"ChromaDB '{RAG_COLLECTION_NAME}' — {self._doc_count} docs")

    def _load_bm25(self) -> None:
        bm25_path = PROJECT_ROOT / RAG_PERSIST_DIR / "bm25_index.pkl"
        if bm25_path.exists():
            try:
                with open(bm25_path, "rb") as fh:
                    payload = pickle.load(fh)
                self._bm25 = payload["bm25"]
                self._bm25_ids = payload["ids"]
                logger.info(f"BM25 index loaded — {len(self._bm25_ids)} docs")
                return
            except Exception as e:
                logger.warning(f"BM25 index corrupt, skipping sparse search: {e}")
        self._bm25 = None
        self._bm25_ids = []
        logger.warning("No BM25 index found. Run scripts/ingest_bare_acts.py to build the index.")

    @property
    def is_ready(self) -> bool:
        self._ensure_initialized()
        return self._doc_count > 0

    def query(
        self,
        query_text: str,
        top_k: int = 5,
        regime_filter: str | None = None,
    ) -> list[RAGResult]:
        """Retrieve top-k sections via hybrid search (dense + sparse + RRF)."""
        self._ensure_initialized()
        if not self.is_ready:
            logger.warning("Local RAG index is empty — returning no results")
            return []

        dense_ids, dense_docs, dense_metas = self._dense_search(
            query_text, top_k=top_k * 3, regime_filter=regime_filter
        )
        sparse_ids = self._sparse_search(
            query_text, top_k=top_k * 3, regime_filter=regime_filter, fallback_ids=dense_ids
        )
        fused = _reciprocal_rank_fusion(dense_ids, sparse_ids)[:top_k]

        id_to_meta = {
            doc_id: (doc, meta)
            for doc_id, doc, meta in zip(dense_ids, dense_docs, dense_metas)
        }
        dense_rank_map = {doc_id: i + 1 for i, doc_id in enumerate(dense_ids)}
        sparse_rank_map = {doc_id: i + 1 for i, doc_id in enumerate(sparse_ids)}

        results: list[RAGResult] = []
        for doc_id, score in fused:
            if doc_id not in id_to_meta:
                continue
            doc_text, meta = id_to_meta[doc_id]
            results.append(RAGResult(
                text=doc_text,
                act=meta.get("act", ""),
                section_number=meta.get("section_number", ""),
                section_title=meta.get("section_title", ""),
                regime=meta.get("regime", ""),
                source_file=meta.get("source_file", ""),
                rrf_score=score,
                dense_rank=dense_rank_map.get(doc_id),
                sparse_rank=sparse_rank_map.get(doc_id),
            ))

        logger.info(
            f"RAG '{query_text[:60]}' → {len(results)} results "
            f"(dense={len(dense_ids)}, sparse={len(sparse_ids)}, regime={regime_filter})"
        )
        return results

    def _dense_search(
        self, query_text: str, top_k: int, regime_filter: str | None
    ) -> tuple[list[str], list[str], list[dict]]:
        where_clause: dict | None = None
        if regime_filter in ("bns_bnss", "ipc_crpc"):
            where_clause = {"regime": {"$eq": regime_filter}}

        kwargs: dict[str, Any] = {
            "query_texts": [query_text],
            "n_results": min(top_k, max(self._doc_count, 1)),
            "include": ["documents", "metadatas", "distances"],
        }
        if where_clause:
            kwargs["where"] = where_clause

        try:
            res = self._collection.query(**kwargs)
        except Exception as e:
            logger.error(f"ChromaDB query failed: {e}")
            return [], [], []

        ids = res.get("ids", [[]])[0]
        docs = res.get("documents", [[]])[0]
        metas = res.get("metadatas", [[]])[0]
        return ids, docs, metas

    def _sparse_search(
        self,
        query_text: str,
        top_k: int,
        regime_filter: str | None,
        fallback_ids: list[str],
    ) -> list[str]:
        if self._bm25 is None or not self._bm25_ids:
            return list(fallback_ids)
        try:
            tokens = query_text.lower().split()
            scores = self._bm25.get_scores(tokens)
            scored = sorted(zip(self._bm25_ids, scores), key=lambda x: x[1], reverse=True)
            return [doc_id for doc_id, _ in scored[:top_k]]
        except Exception as e:
            logger.warning(f"BM25 search failed: {e}")
            return list(fallback_ids)

    def get_stats(self) -> dict[str, Any]:
        self._ensure_initialized()
        return {
            "collection": RAG_COLLECTION_NAME,
            "total_sections": self._doc_count,
            "bm25_docs": len(self._bm25_ids),
            "embed_model": RAG_EMBED_MODEL,
            "persist_dir": str(PROJECT_ROOT / RAG_PERSIST_DIR),
            "is_ready": self.is_ready,
        }


# ---------------------------------------------------------------------------
# Module-level convenience functions
# ---------------------------------------------------------------------------

def get_rag_engine() -> HybridRAGEngine:
    """Return the module-level singleton RAG engine."""
    return HybridRAGEngine()


def query_local_rag(
    query_text: str,
    top_k: int = 5,
    regime_filter: str | None = None,
) -> list[dict[str, Any]]:
    """Convenience wrapper returning Tavily-compatible dicts.

    This allows the search node to treat local RAG and Tavily results
    identically with zero changes to the downstream grader/synthesizer.
    """
    engine = get_rag_engine()
    results = engine.query(query_text, top_k=top_k, regime_filter=regime_filter)
    return [r.to_tavily_compatible() for r in results]
