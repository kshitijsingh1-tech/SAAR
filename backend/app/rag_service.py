"""
Saar — Domain-Agnostic RAG Knowledge Base Service
Provides retrieval-augmented generation across multiple scientific domains.
Supports built-in knowledge bases + custom user-uploaded documents.
"""
import os
import re
import math
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from collections import Counter

# ---------------------------------------------------------------------------
# Data Models
# ---------------------------------------------------------------------------

class KnowledgeChunk:
    """A single retrievable unit of domain knowledge."""
    __slots__ = ("chunk_id", "domain", "source", "section", "content", "tokens", "term_freq")

    def __init__(self, chunk_id: str, domain: str, source: str, section: str, content: str):
        self.chunk_id = chunk_id
        self.domain = domain
        self.source = source
        self.section = section
        self.content = content
        self.tokens: List[str] = _tokenize(content)
        self.term_freq: Counter = Counter(self.tokens)


class RAGResult:
    """A single retrieval result with relevance score."""
    __slots__ = ("chunk", "score")

    def __init__(self, chunk: KnowledgeChunk, score: float):
        self.chunk = chunk
        self.score = score

    @property
    def domain(self) -> str:
        return self.chunk.domain

    @property
    def source(self) -> str:
        return self.chunk.source

    @property
    def section(self) -> str:
        return self.chunk.section

    @property
    def content(self) -> str:
        return self.chunk.content

    def to_dict(self) -> Dict[str, Any]:
        return {
            "chunk_id": self.chunk.chunk_id,
            "domain": self.chunk.domain,
            "source": self.chunk.source,
            "section": self.chunk.section,
            "content": self.chunk.content,
            "relevance_score": round(self.score, 4),
        }


# ---------------------------------------------------------------------------
# Text utilities
# ---------------------------------------------------------------------------

_STOP_WORDS = frozenset(
    "a an the is are was were be been being have has had do does did will would "
    "shall should may might can could of in to for on with at by from as into "
    "through during before after above below between out off over under again "
    "further then once here there when where why how all each every both few "
    "more most other some such no nor not only own same so than too very and "
    "but if or because until while about".split()
)


def _tokenize(text: str) -> List[str]:
    """Lowercase tokenization with stop-word removal."""
    return [w for w in re.findall(r"[a-z0-9]+", text.lower()) if w not in _STOP_WORDS and len(w) > 1]


def _chunk_text(text: str, max_tokens: int = 200, overlap: int = 40) -> List[str]:
    """Split text into overlapping chunks by sentence boundaries."""
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    chunks: List[str] = []
    current: List[str] = []
    current_len = 0

    for sent in sentences:
        sent_len = len(sent.split())
        if current_len + sent_len > max_tokens and current:
            chunks.append(" ".join(current))
            # Keep last few sentences for overlap
            overlap_sents: List[str] = []
            overlap_len = 0
            for s in reversed(current):
                if overlap_len + len(s.split()) > overlap:
                    break
                overlap_sents.insert(0, s)
                overlap_len += len(s.split())
            current = overlap_sents
            current_len = overlap_len
        current.append(sent)
        current_len += sent_len

    if current:
        chunks.append(" ".join(current))
    return chunks


# ---------------------------------------------------------------------------
# RAG Knowledge Base Service
# ---------------------------------------------------------------------------

class RAGKnowledgeService:
    """
    Multi-domain RAG knowledge base with TF-IDF/BM25 retrieval.
    Loads built-in domain knowledge files and supports custom uploads.
    """

    def __init__(self):
        self.chunks: List[KnowledgeChunk] = []
        self.domains: Dict[str, List[KnowledgeChunk]] = {}
        self.doc_freq: Counter = Counter()
        self.total_docs: int = 0
        self._load_builtin_knowledge()

    # ----- Public API -----

    def list_domains(self) -> List[Dict[str, Any]]:
        """List all available knowledge base domains."""
        result = []
        for domain, chunks in self.domains.items():
            sources = list({c.source for c in chunks})
            result.append({
                "domain": domain,
                "chunk_count": len(chunks),
                "sources": sources,
            })
        return result

    def query(
        self,
        query_text: str,
        domain: Optional[str] = None,
        top_k: int = 5,
    ) -> List[RAGResult]:
        """Retrieve the most relevant knowledge chunks for a query."""
        query_tokens = _tokenize(query_text)
        if not query_tokens:
            return []

        candidates = self.domains.get(domain, self.chunks) if domain else self.chunks
        if not candidates:
            return []

        scored: List[Tuple[float, KnowledgeChunk]] = []
        for chunk in candidates:
            score = self._bm25_score(query_tokens, chunk)
            if score > 0:
                scored.append((score, chunk))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [RAGResult(chunk=c, score=s) for s, c in scored[:top_k]]

    def ingest_text(self, text: str, domain: str, source: str = "user_upload") -> int:
        """Ingest raw text into a domain knowledge base. Returns chunk count."""
        raw_chunks = _chunk_text(text)
        added = 0
        for i, content in enumerate(raw_chunks):
            cid = hashlib.md5(f"{domain}:{source}:{i}:{content[:64]}".encode()).hexdigest()[:12]
            chunk = KnowledgeChunk(
                chunk_id=cid,
                domain=domain,
                source=source,
                section=f"Section {i + 1}",
                content=content,
            )
            self.chunks.append(chunk)
            self.domains.setdefault(domain, []).append(chunk)
            for token in set(chunk.tokens):
                self.doc_freq[token] += 1
            self.total_docs += 1
            added += 1
        return added

    # ----- BM25 scoring -----

    def _bm25_score(self, query_tokens: List[str], chunk: KnowledgeChunk, k1: float = 1.5, b: float = 0.75) -> float:
        if not chunk.tokens:
            return 0.0
        avg_dl = max(1, sum(len(c.tokens) for c in self.chunks) // max(1, len(self.chunks)))
        dl = len(chunk.tokens)
        score = 0.0
        for qt in query_tokens:
            tf = chunk.term_freq.get(qt, 0)
            if tf == 0:
                continue
            df = self.doc_freq.get(qt, 0)
            idf = math.log((self.total_docs - df + 0.5) / (df + 0.5) + 1.0)
            tf_norm = (tf * (k1 + 1)) / (tf + k1 * (1 - b + b * dl / avg_dl))
            score += idf * tf_norm
        return score

    # ----- Built-in knowledge loader -----

    def _load_builtin_knowledge(self):
        """Load pre-packaged domain knowledge from the knowledge/ directory."""
        kb_dir = Path(__file__).parent / "knowledge"
        if not kb_dir.exists():
            return
        for md_file in sorted(kb_dir.glob("*.md")):
            domain = md_file.stem.replace("_kb", "").replace("_", " ").strip()
            text = md_file.read_text(encoding="utf-8", errors="ignore")
            # Split by markdown headings for better section labeling
            sections = re.split(r"\n#{1,3}\s+", text)
            headings = re.findall(r"\n(#{1,3}\s+.+)", text)
            headings.insert(0, domain.title())

            for idx, section_text in enumerate(sections):
                section_text = section_text.strip()
                if len(section_text) < 20:
                    continue
                heading = headings[idx].strip().lstrip("#").strip() if idx < len(headings) else f"Section {idx}"
                sub_chunks = _chunk_text(section_text, max_tokens=200, overlap=40)
                for ci, content in enumerate(sub_chunks):
                    cid = hashlib.md5(f"{domain}:{md_file.name}:{idx}:{ci}".encode()).hexdigest()[:12]
                    chunk = KnowledgeChunk(
                        chunk_id=cid,
                        domain=domain,
                        source=md_file.name,
                        section=heading,
                        content=content,
                    )
                    self.chunks.append(chunk)
                    self.domains.setdefault(domain, []).append(chunk)
                    for token in set(chunk.tokens):
                        self.doc_freq[token] += 1
                    self.total_docs += 1
