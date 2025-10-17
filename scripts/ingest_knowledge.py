from __future__ import annotations

import argparse
import asyncio
from pathlib import Path
from typing import Iterable, Optional

import httpx
from sqlalchemy import select, text

from backend.app.core.config import settings
from backend.app.db.models import KnowledgeItem
from backend.app.db.session import SessionLocal, engine


def read_files(paths: Iterable[Path]) -> list[tuple[str, str]]:
    items: list[tuple[str, str]] = []
    for p in paths:
        if not p.exists() or not p.is_file():
            continue
        content = p.read_text(encoding="utf-8", errors="ignore")
        title = p.stem.replace("_", " ").strip() or str(p)
        items.append((title, content))
    return items


async def summarize(text_in: str, model: Optional[str] = None) -> str:
    """Summarize using a local LLM (Ollama). Falls back to original text on error."""
    model_name = model or settings.llm_model
    if not settings.llm_enabled:
        return text_in

    # Keep prompt compact; chunk if extremely large
    max_len = 8000
    text_slice = text_in[:max_len]
    prompt = (
        "Summarize the following training content into 5-10 sentences in a friendly, "
        "evidence-based tone. Include 1-2 actionable tips. Avoid medical claims.\n\n" + text_slice
    )
    payload = {"model": model_name, "prompt": prompt, "stream": False}

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(settings.llm_base_url, json=payload)
            resp.raise_for_status()
            data = resp.json()
            return (data.get("response") or data.get("text") or "").strip() or text_in
    except Exception:
        return text_in


async def ingest_local_files(
    files: list[Path], tags: Optional[str], source_url: Optional[str], do_summarize: bool
) -> int:
    pairs = read_files(files)
    if not pairs:
        return 0

    # Ensure main tables exist (useful for raw SQLite dev)
    KnowledgeItem.__table__.create(bind=engine, checkfirst=True)

    inserted = 0
    async def process_item(title: str, raw: str) -> tuple[str, str]:
        if do_summarize:
            summary = await summarize(raw)
            return title, summary
        return title, raw

    processed: list[tuple[str, str]] = []
    for t, r in pairs:
        processed.append(await process_item(t, r))

    with SessionLocal() as session:
        for title, content in processed:
            # Skip empties
            if not content.strip():
                continue
            exists = session.execute(
                select(KnowledgeItem).where(KnowledgeItem.title == title)
            ).scalar_one_or_none()
            if exists:
                # Update content/tags/source if changed
                exists.content = content
                if tags:
                    exists.tags = tags
                if source_url:
                    exists.source_url = source_url
            else:
                session.add(
                    KnowledgeItem(
                        title=title,
                        content=content,
                        source_url=source_url,
                        tags=tags,
                    )
                )
                inserted += 1
        session.commit()

        # Backfill FTS, best-effort
        try:
            session.execute(
                text(
                    "INSERT INTO knowledge_fts(rowid, title, content, tags) "
                    "SELECT id, title, content, tags FROM knowledge_items "
                    "WHERE rowid NOT IN (SELECT rowid FROM knowledge_fts)"
                )
            )
            session.commit()
        except Exception:
            pass

    return inserted


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest local files into knowledge base")
    parser.add_argument(
        "--file",
        dest="files",
        action="append",
        help="Path to a .txt/.md file (can be repeated)",
    )
    parser.add_argument(
        "--tags",
        type=str,
        default=None,
        help="Comma-separated tags (e.g., 'jeff nippard,hypertrophy')",
    )
    parser.add_argument("--source-url", type=str, default=None, help="Optional source URL")
    parser.add_argument(
        "--no-summarize",
        action="store_true",
        help="Do not summarize with local LLM; store raw content",
    )
    # Explicitly opt-out of network fetching; this script is local-only by default.
    # YouTube/transcript support can be added with an --allow-network flag in the future.

    args = parser.parse_args()

    files = [Path(f) for f in (args.files or [])]
    tags: Optional[str] = args.tags
    source_url: Optional[str] = args.source_url
    do_summarize = not args.no_summarize

    inserted = asyncio.run(
        ingest_local_files(files=files, tags=tags, source_url=source_url, do_summarize=do_summarize)
    )
    print(f"Ingestion complete. Inserted/updated {inserted} new items.")


if __name__ == "__main__":
    main()
