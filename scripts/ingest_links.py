from __future__ import annotations

import argparse
import asyncio
import re
import sys
from pathlib import Path
from typing import Optional

import httpx
import trafilatura
from sqlalchemy import select, text

# Ensure project root on sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from backend.app.core.config import settings  # noqa: E402
from backend.app.db.models import KnowledgeItem  # noqa: E402
from backend.app.db.session import SessionLocal, engine  # noqa: E402
# isort: skip_file


YOUTUBE_RE = re.compile(r"(?:v=|youtu\.be/)([A-Za-z0-9_-]{11})")


def extract_youtube_id(url: str) -> Optional[str]:
    m = YOUTUBE_RE.search(url)
    return m.group(1) if m else None


# Simple keyword → canonical tag mapping for MVP
CANONICAL_TAGS = {
    "lean": ["lean", "cut", "fat loss", "fat-loss", "cutting"],
    "bulk": ["bulk", "bulking", "gain", "mass", "gaining"],
    "hypertrophy": ["hypertrophy", "muscle growth", "grow muscle"],
    "strength": ["strength", "1rm", "one-rep", "powerlifting", "intensity"],
    "arms": ["arm", "arms"],
    "biceps": ["bicep", "biceps", "curl"],
    "triceps": ["tricep", "triceps", "pressdown", "skullcrusher"],
    "shoulders": ["shoulder", "shoulders", "ohp", "overhead press", "lateral raise"],
    "chest": ["chest", "bench"],
    "back": ["back", "row", "pull-up", "pullup", "pulldown"],
    "lats": ["lat", "lats"],
    "legs": ["leg", "legs", "lower body"],
    "quads": ["quad", "quads", "leg extension"],
    "hamstrings": ["hamstring", "hamstrings", "leg curl", "rdl"],
    "glutes": ["glute", "glutes", "hip thrust"],
    "calves": ["calf", "calves"],
    "abs": ["abs", "core", "abdominals", "plank"],
    "upper": ["upper"],
    "lower": ["lower"],
    "push": ["push"],
    "pull": ["pull"],
}


def auto_tags_for(text: str) -> set[str]:
    tags: set[str] = set()
    blob = text.lower()
    for canon, keywords in CANONICAL_TAGS.items():
        for kw in keywords:
            if kw in blob:
                tags.add(canon)
                break
    return tags


async def summarize(text_in: str, model: Optional[str] = None) -> str:
    model_name = model or settings.llm_model
    if not settings.llm_enabled:
        return text_in
    text_slice = text_in[:8000]
    prompt = (
        "Summarize the article/transcript into 5-10 sentences in a friendly, evidence-based tone. "
        "Include 1-2 actionable tips. Avoid medical claims.\n\n" + text_slice
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


def fetch_article_text(url: str) -> Optional[str]:
    try:
        downloaded = trafilatura.fetch_url(url)
        if not downloaded:
            return None
        extracted = trafilatura.extract(downloaded, include_comments=False, include_tables=False)
        return extracted
    except Exception:
        return None


def fetch_youtube_transcript_text(video_id: str) -> Optional[str]:
    try:
        from youtube_transcript_api import YouTubeTranscriptApi  # local import

        segments = YouTubeTranscriptApi.get_transcript(video_id, languages=["en"])
        text = " ".join(seg.get("text", "") for seg in segments)
        return text or None
    except Exception:
        return None


async def ingest_url(
    url: str, tags: Optional[str], do_summarize: bool, store_transcript: bool, use_auto_tags: bool
) -> int:
    KnowledgeItem.__table__.create(bind=engine, checkfirst=True)

    title_base = url
    raw: Optional[str] = None

    vid = extract_youtube_id(url)
    if vid:
        raw = fetch_youtube_transcript_text(vid)
        # fallback to page extraction if transcript unavailable
        if not raw:
            raw = fetch_article_text(url)
        if not raw:
            return 0
        title_base = f"YouTube: {vid}"
    else:
        raw = fetch_article_text(url)
        if not raw:
            return 0
        # Trafilatura sometimes gives title; we keep URL as source of truth for now

    content_summary = await summarize(raw) if do_summarize else raw

    # Compute final tags
    provided = set(t.strip() for t in (tags.split(",") if tags else []) if t.strip())
    inferred = (
        auto_tags_for((content_summary or "") + "\n" + (raw or ""))
        if use_auto_tags
        else set()
    )
    final_tags = sorted(provided.union(inferred))
    tags_str = ",".join(final_tags) if final_tags else None

    with SessionLocal() as session:
        # Upsert summary item
        summary_title = f"{title_base} – Summary"
        exists = session.execute(
            select(KnowledgeItem).where(
                (KnowledgeItem.source_url == url) & (KnowledgeItem.title == summary_title)
            )
        ).scalar_one_or_none()
        if exists:
            exists.content = content_summary
            exists.tags = tags_str
        else:
            session.add(
                KnowledgeItem(
                    title=summary_title, content=content_summary, source_url=url, tags=tags_str
                )
            )

        # Optionally store raw transcript/article as separate item
        if store_transcript and raw:
            transcript_title = f"{title_base} – Transcript"
            transcript_tagset = set(final_tags)
            transcript_tagset.add("transcript")
            transcript_tags = ",".join(sorted(transcript_tagset))
            existing_trans = session.execute(
                select(KnowledgeItem).where(
                    (KnowledgeItem.source_url == url) & (KnowledgeItem.title == transcript_title)
                )
            ).scalar_one_or_none()
            if existing_trans:
                existing_trans.content = raw
                existing_trans.tags = transcript_tags
            else:
                session.add(
                    KnowledgeItem(
                        title=transcript_title, content=raw, source_url=url, tags=transcript_tags
                    )
                )
        session.commit()

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

    return 1


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Ingest URLs (articles/YouTube) into knowledge base"
    )
    parser.add_argument("--url", action="append", help="URL to ingest (repeatable)")
    parser.add_argument("--tags", type=str, default=None, help="Comma-separated tags")
    parser.add_argument(
        "--no-summarize", action="store_true", help="Store raw text without LLM summary"
    )
    parser.add_argument(
        "--store-transcript",
        action="store_true",
        help="Also store full transcript/article as a separate knowledge item",
    )
    parser.add_argument(
        "--auto-tags",
        action="store_true",
        help="Infer tags from content (e.g., lean, bulk, strength, arms, back, legs, etc)",
    )

    args = parser.parse_args()
    urls = args.url or []
    tags = args.tags
    do_summarize = not args.no_summarize
    store_transcript = args.store_transcript
    use_auto_tags = args.auto_tags

    inserted = 0
    for u in urls:
        inserted += asyncio.run(ingest_url(u, tags, do_summarize, store_transcript, use_auto_tags))
    print(f"Ingestion complete. Inserted/updated {inserted} items.")


if __name__ == "__main__":
    main()
