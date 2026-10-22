"""RAG (Retrieval-Augmented Generation) Knowledge Base using ChromaDB.

Indexes and retrieves contractual Carrier SLA Agreements, operational refund rules,
and delivery compliance standards to ground AI analytics responses in official policies.
"""

from __future__ import annotations

import logging
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

import chromadb
from chromadb.api.types import Documents, EmbeddingFunction, Embeddings

from src.config import settings

logger = logging.getLogger(__name__)

COLLECTION_NAME = "carrier_sla_policies"


class ResilientFallbackEmbeddingFunction(EmbeddingFunction[Documents]):
    """Deterministic, zero-network fallback embedding function ensuring test stability offline."""

    def __init__(self, dim: int = 128) -> None:
        self.dim = dim

    def __call__(self, input: Documents) -> Embeddings:
        embeddings: List[List[float]] = []
        for doc in input:
            tokens = re.findall(r"\w+", doc.lower())
            vec = [0.0] * self.dim
            if not tokens:
                embeddings.append(vec)
                continue
            for token in tokens:
                idx = abs(hash(token)) % self.dim
                vec[idx] += 1.0
            norm = sum(v * v for v in vec) ** 0.5
            if norm > 0:
                vec = [v / norm for v in vec]
            embeddings.append(vec)
        return embeddings


def get_embedding_function() -> EmbeddingFunction[Documents]:
    """Provide embedding function: default ONNX all-MiniLM-L6-v2 with offline fallback."""
    try:
        from chromadb.utils.embedding_functions import DefaultEmbeddingFunction
        fn = DefaultEmbeddingFunction()
        # Verify it works
        fn(["test probe"])
        return fn
    except Exception as exc:
        logger.warning("DefaultEmbeddingFunction failed, using resilient fallback: %s", exc)
        return ResilientFallbackEmbeddingFunction()


@dataclass
class PolicyChunk:
    """Document chunk representing a discrete policy clause or section."""
    id: str
    title: str
    text: str
    metadata: Dict[str, Any]


def load_and_chunk_markdown_policies(policies_dir: str) -> List[PolicyChunk]:
    """Parse policy markdown files in policies_dir into semantic chunks with hierarchical parent context."""
    dir_path = Path(policies_dir)
    if not dir_path.exists():
        logger.warning("Policies directory not found: %s", dir_path)
        return []

    chunks: List[PolicyChunk] = []

    for file_path in dir_path.glob("*.md"):
        try:
            content = file_path.read_text(encoding="utf-8")
        except Exception as exc:
            logger.error("Failed to read policy file %s: %s", file_path, exc)
            continue

        file_name = file_path.name
        raw_sections = re.split(r"\n(?=#{2,3}\s+)", content)
        parent_h2 = ""

        for idx, section in enumerate(raw_sections):
            clean_section = section.strip()
            if not clean_section or clean_section == "---":
                continue

            lines = clean_section.splitlines()
            first_line = lines[0].strip()

            is_h2 = first_line.startswith("## ")
            is_h3 = first_line.startswith("### ")

            if is_h2:
                parent_h2 = first_line.lstrip("#").strip()
                # If section only has header and no substantial body (e.g. followed immediately by h3)
                body_lines = [l for l in lines[1:] if l.strip() and not l.strip().startswith("---")]
                if not body_lines:
                    continue

            header_match = re.match(r"^#{2,3}\s+(.+)$", first_line)
            title = header_match.group(1).strip() if header_match else f"Section {idx+1}"

            # Prepend parent h2 context if it's an h3 subsection
            chunk_text = f"[{parent_h2}] {clean_section}" if (is_h3 and parent_h2) else clean_section

            # Detect carriers mentioned
            carriers = []
            for c in ["C01", "C02", "C03"]:
                if c in clean_section:
                    carriers.append(c)
            carriers_str = ", ".join(carriers) if carriers else "all"

            # Detect topic
            lowered = clean_section.lower()
            if "sla" in lowered or "on-time" in lowered or "ketepatan" in lowered:
                topic = "sla_target"
            elif "refund" in lowered or "ganti rugi" in lowered or "penalti" in lowered or "reimbursement" in lowered:
                topic = "refund_policy"
            elif "sanction" in lowered or "sanksi" in lowered:
                topic = "contractual_sanctions"
            else:
                topic = "general_policy"

            chunk_id = f"{file_path.stem}_{idx+1}"
            chunks.append(
                PolicyChunk(
                    id=chunk_id,
                    title=title,
                    text=chunk_text,
                    metadata={
                        "source": file_name,
                        "title": title,
                        "carriers": carriers_str,
                        "topic": topic,
                    },
                )
            )

    return chunks


class PolicyVectorStore:
    """Singleton wrapper around ChromaDB persistent vector store for logistics policies."""

    def __init__(self, persist_dir: Optional[str] = None) -> None:
        self.persist_dir = persist_dir or settings.CHROMA_PERSIST_DIR
        Path(self.persist_dir).mkdir(parents=True, exist_ok=True)

        self.client = chromadb.PersistentClient(path=self.persist_dir)
        self.embedding_fn = get_embedding_function()
        self.collection = self.client.get_or_create_collection(
            name=COLLECTION_NAME,
            embedding_function=self.embedding_fn,
        )

        self._ensure_indexed()

    def _ensure_indexed(self) -> None:
        """Index policies into collection with upsert."""
        try:
            chunks = load_and_chunk_markdown_policies(settings.POLICIES_DIR)
            if not chunks:
                logger.warning("No policy chunks discovered in %s", settings.POLICIES_DIR)
                return

            ids = [c.id for c in chunks]
            documents = [c.text for c in chunks]
            metadatas = [c.metadata for c in chunks]

            self.collection.upsert(
                ids=ids,
                documents=documents,
                metadatas=metadatas,
            )
            logger.info("Successfully indexed/updated %d policy chunks in ChromaDB.", len(chunks))
        except Exception as exc:
            logger.error("Failed to ensure ChromaDB policy indexing: %s", exc)

    def search(
        self,
        query: str,
        top_k: int = 4,
        carrier_filter: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Perform semantic search against indexed logistics policies."""
        try:
            where_filter = None
            if carrier_filter and carrier_filter in ["C01", "C02", "C03"]:
                pass

            results = self.collection.query(
                query_texts=[query],
                n_results=min(top_k, max(1, self.collection.count())),
                where=where_filter,
            )

            matched_chunks: List[Dict[str, Any]] = []
            if results and results.get("documents") and results["documents"][0]:
                docs = results["documents"][0]
                metadatas = results["metadatas"][0] if results.get("metadatas") else [{}] * len(docs)
                ids = results["ids"][0] if results.get("ids") else [""] * len(docs)

                for doc, meta, cid in zip(docs, metadatas, ids):
                    matched_chunks.append({
                        "id": cid,
                        "title": meta.get("title", "Policy Section"),
                        "text": doc,
                        "source": meta.get("source", "carrier_sla_agreements.md"),
                        "carriers": meta.get("carriers", "all"),
                        "topic": meta.get("topic", "policy"),
                    })

            return matched_chunks
        except Exception as exc:
            logger.error("Error querying ChromaDB vector store: %s", exc)
            return []


# Global singleton instance
_vector_store: Optional[PolicyVectorStore] = None


def get_vector_store() -> PolicyVectorStore:
    """Retrieve or initialize the global PolicyVectorStore singleton."""
    global _vector_store
    if _vector_store is None:
        _vector_store = PolicyVectorStore()
    return _vector_store


def search_carrier_policies(query: str, top_k: int = 4) -> List[Dict[str, Any]]:
    """Public helper to search carrier policies via ChromaDB."""
    store = get_vector_store()
    return store.search(query=query, top_k=top_k)


def format_policy_grounding(policy_matches: List[Dict[str, Any]]) -> str:
    """Format retrieved policy clauses into a clean grounding string for LLM and user display."""
    if not policy_matches:
        return ""

    lines = ["**Rujukan Kebijakan & Kontrak (Grounding Policy):**"]
    for item in policy_matches:
        title = item.get("title", "Pasal Kebijakan")
        source = item.get("source", "carrier_sla_agreements.md")
        lines.append(f"- **{title}** (`docs/policies/{source}`):")
        # Extract the core sentences
        snippet = item.get("text", "").strip()
        lines.append(f"  > {snippet.replace(chr(10), chr(10) + '  > ')}")

    return "\n\n".join(lines)
