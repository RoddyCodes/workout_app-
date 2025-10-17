from __future__ import annotations

import json
import sys
from pathlib import Path

from sqlalchemy import select, text

# Ensure project root on sys.path to import backend package when executed directly
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from backend.app.db.models import KnowledgeItem, WorkoutTemplate  # noqa: E402
from backend.app.db.session import SessionLocal, engine  # noqa: E402


def main() -> None:
    # Resolve data path relative to repo root
    repo_root = Path(__file__).resolve().parents[1]
    data_path = repo_root / "backend" / "app" / "data" / "workouts.json"
    if not data_path.exists():
        raise FileNotFoundError(f"Expected data file at {data_path}")

    with data_path.open("r", encoding="utf-8") as f:
        payload = json.load(f)

    templates = payload.get("templates", [])

    # Ensure table exists (useful for local dev with SQLite)
    WorkoutTemplate.__table__.create(bind=engine, checkfirst=True)

    inserted = 0
    with SessionLocal() as session:
        for tpl in templates:
            tpl_id = tpl["id"]
            exists = session.scalar(select(WorkoutTemplate).where(WorkoutTemplate.id == tpl_id))
            if exists:
                continue
            row = WorkoutTemplate(
                id=tpl_id,
                name=tpl.get("name", tpl_id),
                goal=tpl.get("goal", "unknown"),
                experience_level=tpl.get("experience_level", "unknown"),
                payload=json.dumps(tpl),
            )
            session.add(row)
            inserted += 1
        session.commit()

    # Seed knowledge items from templates (overview + notes)
    knowledge_inserted = 0
    with SessionLocal() as session:
        for tpl in templates:
            title = f"{tpl.get('name', tpl['id'])} – Overview"
            # Combine description + coaching notes into a single knowledge chunk
            description = tpl.get("description", "")
            notes = tpl.get("coaching_notes", [])
            combined = description
            if notes:
                combined += "\n\nCoaching notes:\n- " + "\n- ".join(notes)

            exists = session.execute(
                select(KnowledgeItem).where(KnowledgeItem.title == title)
            ).scalar_one_or_none()
            if exists:
                continue
            ki = KnowledgeItem(
                title=title,
                content=combined,
                source_url=f"internal:workouts.json#{tpl['id']}",
                tags=",".join(filter(None, [tpl.get("goal"), tpl.get("experience_level")])) or None,
            )
            session.add(ki)
            knowledge_inserted += 1
        session.commit()

        # Backfill FTS index if present
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

    # Ingest curated knowledge JSON files
    kb_dir = repo_root / "backend" / "app" / "data" / "knowledge"
    curated_inserted = 0
    if kb_dir.exists():
        files = sorted(kb_dir.glob("*.json"))
        with SessionLocal() as session:
            for jf in files:
                with jf.open("r", encoding="utf-8") as fh:
                    try:
                        item = json.load(fh)
                    except Exception:
                        continue
                title = item.get("title")
                content = item.get("content", "").strip()
                source_url = item.get("source_url")
                tags_arr = item.get("tags") or []
                tags = ",".join(tags_arr) if isinstance(tags_arr, list) else (tags_arr or None)
                if not title or not content:
                    continue
                exists = session.execute(
                    select(KnowledgeItem).where(KnowledgeItem.title == title)
                ).scalar_one_or_none()
                if exists:
                    continue
                session.add(
                    KnowledgeItem(
                        title=title,
                        content=content,
                        source_url=source_url,
                        tags=tags,
                    )
                )
                curated_inserted += 1
            session.commit()

    print(
        (
            "Seed complete. Inserted {} templates, {} knowledge items from templates, "
            "and {} curated knowledge items. Data path: {}"
        ).format(inserted, knowledge_inserted, curated_inserted, data_path)
    )


if __name__ == "__main__":
    main()
