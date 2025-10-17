from __future__ import annotations
# isort: skip_file

import re
from typing import List, Tuple

import httpx
from sqlalchemy import or_, select, text
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.db.models import KnowledgeItem
from backend.app.schemas.chat import ChatResponse, ChatSource


_STOPWORDS = {
    "the",
    "is",
    "a",
    "an",
    "and",
    "or",
    "of",
    "to",
    "in",
    "for",
    "on",
    "with",
    "at",
    "by",
    "what",
    "who",
    "when",
    "how",
    "why",
    "are",
    "his",
    "her",
    "their",
}


def _keywords_from_query(query: str, max_tokens: int = 8) -> List[str]:
    # Lowercase, strip punctuation, split, remove stopwords/short tokens
    tokens = re.findall(r"[a-zA-Z][a-zA-Z\-]{1,}\b", query.lower())
    filtered = [t for t in tokens if t not in _STOPWORDS and len(t) > 2]
    # Deduplicate preserving order
    seen = set()
    uniq: List[str] = []
    for t in filtered:
        if t not in seen:
            seen.add(t)
            uniq.append(t)
    return uniq[:max_tokens]


def retrieve_knowledge(
    session: Session, query: str, top_k: int = 3
) -> List[Tuple[KnowledgeItem, float]]:
    """Simple retrieval using SQLite FTS5 when available; falls back to LIKE search.
    Returns list of (KnowledgeItem, score)
    """
    # Build relaxed token query to improve recall
    tokens = _keywords_from_query(query)
    fts_query = " OR ".join(tokens) if tokens else query

    # Try FTS5 (searches title/content/tags)
    try:
        rows = session.execute(
            text(
                (
                    "SELECT ki.id, ki.title, ki.content, ki.source_url, ki.tags, "
                    "bm25(knowledge_fts) as score\n"
                )
                + "FROM knowledge_fts JOIN knowledge_items ki ON knowledge_fts.rowid = ki.id\n"
                + "WHERE knowledge_fts MATCH :q ORDER BY score LIMIT :k"
            ),
            {"q": fts_query, "k": top_k},
        ).all()
        results: List[Tuple[KnowledgeItem, float]] = []
        for rid, title, content, source_url, tags, score in rows:
            item = KnowledgeItem(
                id=rid, title=title, content=content, source_url=source_url, tags=tags
            )
            results.append((item, float(score)))
        if results:
            return results
    except Exception:
        # Fallback to LIKE search
        pass

    # Broaden LIKE over tokens across title/content/tags using OR
    if tokens:
        like_conditions = []
        for t in tokens:
            pat = f"%{t}%"
            like_conditions.extend(
                [
                    KnowledgeItem.title.ilike(pat),
                    KnowledgeItem.content.ilike(pat),
                    KnowledgeItem.tags.ilike(pat),
                ]
            )
        stmt = select(KnowledgeItem).where(or_(*like_conditions)).limit(top_k)
    else:
        stmt = select(KnowledgeItem).where(KnowledgeItem.content.ilike(f"%{query}%")).limit(top_k)

    like_rows = session.execute(stmt).scalars()
    return [(row, 1.0) for row in like_rows]


async def call_llm(prompt: str) -> str:
    if not settings.llm_enabled:
        raise RuntimeError("LLM disabled")

    payload = {
        "model": settings.llm_model,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0.7},
    }
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(settings.llm_base_url, json=payload)
        resp.raise_for_status()
        data = resp.json()
        # Ollama returns {'response': '...'}
        return data.get("response") or data.get("text") or ""


def build_prompt(
    user_message: str, docs: List[Tuple[KnowledgeItem, float]]
) -> Tuple[str, List[ChatSource]]:
    context_lines = []
    sources: List[ChatSource] = []
    for i, (doc, score) in enumerate(docs, start=1):
        snippet = doc.content.strip()
        # Keep it compact
        if len(snippet) > 500:
            snippet = snippet[:500] + "..."
        context_lines.append(f"[{i}] Title: {doc.title}\n{snippet}")
        sources.append(ChatSource(title=doc.title, url=doc.source_url, score=score))

    persona = (
        "You are a friendly gym buddy who speaks in a supportive, concise tone. "
        "Ground your advice in evidence-based strength training principles (Jeff Nippard style). "
        "Be practical, avoid medical claims, and include 1-2 short actionable suggestions. "
        "Cite sources with bracket numbers like [1], [2] that refer to the provided context items."
    )

    prompt = (
        f"System: {persona}\n\n"
        f"Context sources (use for citations):\n{chr(10).join(context_lines)}\n\n"
        f"User: {user_message}\n\nAssistant:"
    )
    return prompt, sources


async def chat(session: Session, message: str, top_k: int = 3) -> ChatResponse:
    docs = retrieve_knowledge(session, message, top_k=top_k)
    prompt, sources = build_prompt(message, docs)

    try:
        answer = await call_llm(prompt)
        if not answer.strip():
            raise RuntimeError("Empty LLM response")
        return ChatResponse(answer=answer.strip(), sources=sources, model=settings.llm_model)
    except Exception:
        # Fallback: retrieval-only concise summary
        if not docs:
            return ChatResponse(
                answer=(
                    "I don't have enough context yet to answer that. Try asking about hypertrophy, "
                    "strength, or beginner routines."
                ),
                sources=[],
                model=None,
            )
        # Build a friendly summary from top docs
        bullets = []
        for doc, _ in docs[:2]:
            bullets.append(f"- {doc.title}")
        fallback = (
            "Here’s a quick, evidence-based take based on what I have: \n" + "\n".join(bullets) +
            "\n(Enable a local LLM like Ollama for a fuller, chatty answer with citations.)"
        )
        return ChatResponse(answer=fallback, sources=sources, model=None)
