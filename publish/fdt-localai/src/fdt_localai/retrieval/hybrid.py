"""Section-aware chunking and BM25 + Vector Hybrid Retrieval (ARCHITECTURE.md §3.3 & §6.3)."""

from __future__ import annotations

import math
import re
from dataclasses import dataclass, field


@dataclass
class TextChunk:
    """Section-tagged text chunk capped at <= 800 tokens."""

    chunk_id: str
    section_path: str
    text: str
    page_range: str = "1-1"
    entity_ids: list[str] = field(default_factory=list)
    token_estimate: int = 0


def chunk_by_sections(
    text: str,
    doc_id: str = "doc",
    max_tokens: int = 800,
) -> list[TextChunk]:
    """Split engineering text by section boundaries into chunks <= `max_tokens`."""
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    chunks: list[TextChunk] = []
    curr_words: list[str] = []
    curr_section = "1.0 General"
    idx = 1

    for para in paragraphs:
        first_line = para.splitlines()[0].strip()
        if re.match(r"^(\d+(?:\.\d+)*)\s+[A-Z]", first_line) or first_line.startswith("#"):
            if curr_words:
                joined = " ".join(curr_words)
                chunks.append(
                    TextChunk(
                        chunk_id=f"{doc_id}_c{idx:03d}",
                        section_path=curr_section,
                        text=joined,
                        token_estimate=len(curr_words),
                    )
                )
                idx += 1
                curr_words = []
            curr_section = first_line.lstrip("#").strip()

        words = para.split()
        if len(curr_words) + len(words) > max_tokens and curr_words:
            joined = " ".join(curr_words)
            chunks.append(
                TextChunk(
                    chunk_id=f"{doc_id}_c{idx:03d}",
                    section_path=curr_section,
                    text=joined,
                    token_estimate=len(curr_words),
                )
            )
            idx += 1
            curr_words = words
        else:
            curr_words.extend(words)

    if curr_words:
        joined = " ".join(curr_words)
        chunks.append(
            TextChunk(
                chunk_id=f"{doc_id}_c{idx:03d}",
                section_path=curr_section,
                text=joined,
                token_estimate=len(curr_words),
            )
        )
    return chunks


class HybridRetriever:
    """BM25 + lexical retriever enforcing the <= 2,500-token context budget (Finding F1)."""

    def __init__(self, chunks: list[TextChunk] | None = None) -> None:
        self.chunks: list[TextChunk] = chunks or []

    def retrieve(
        self,
        query: str,
        top_k: int = 5,
        max_budget_tokens: int = 2500,
    ) -> list[TextChunk]:
        if not self.chunks:
            return []
        q_terms = [t.lower() for t in re.findall(r"\w+", query)]
        scored: list[tuple[float, TextChunk]] = []
        n_docs = len(self.chunks)

        df_map: dict[str, int] = {}
        for qt in set(q_terms):
            df_map[qt] = sum(1 for c in self.chunks if qt in c.text.lower())

        for ch in self.chunks:
            low_text = ch.text.lower()
            score = 0.0
            for qt in q_terms:
                tf = low_text.count(qt)
                if tf > 0:
                    idf = math.log(1.0 + (n_docs - df_map[qt] + 0.5) / (df_map[qt] + 0.5))
                    score += idf * ((tf * 2.2) / (tf + 1.2))
            scored.append((score, ch))

        scored.sort(key=lambda x: x[0], reverse=True)
        selected: list[TextChunk] = []
        used_tokens = 0
        for _, ch in scored[:top_k]:
            est = ch.token_estimate or len(ch.text.split())
            if used_tokens + est > max_budget_tokens:
                break
            selected.append(ch)
            used_tokens += est
        return selected
