"""add knowledge_items and FTS5

Revision ID: 0002_knowledge_fts
Revises: 0001_create_workout_templates
Create Date: 2025-10-17
"""
from __future__ import annotations
# isort: skip_file

from alembic import op
import sqlalchemy as sa

revision = "0002_knowledge_fts"
down_revision = "0001_create_workout_templates"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "knowledge_items",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("source_url", sa.String(length=500), nullable=True),
        sa.Column("tags", sa.String(length=200), nullable=True),
    )
    op.create_index("ix_knowledge_title", "knowledge_items", ["title"], unique=False)

    # SQLite FTS5 virtual table linked to knowledge_items
    op.execute(
        """
        CREATE VIRTUAL TABLE IF NOT EXISTS knowledge_fts USING fts5(
            title, content, tags, content='knowledge_items', content_rowid='id'
        );
        """
    )

    # Triggers to keep FTS in sync
    op.execute(
        """
        CREATE TRIGGER IF NOT EXISTS knowledge_ai AFTER INSERT ON knowledge_items BEGIN
            INSERT INTO knowledge_fts(rowid, title, content, tags)
            VALUES (new.id, new.title, new.content, new.tags);
        END;
        """
    )
    op.execute(
        """
        CREATE TRIGGER IF NOT EXISTS knowledge_ad AFTER DELETE ON knowledge_items BEGIN
            INSERT INTO knowledge_fts(knowledge_fts, rowid, title, content, tags)
            VALUES('delete', old.id, old.title, old.content, old.tags);
        END;
        """
    )
    op.execute(
        """
        CREATE TRIGGER IF NOT EXISTS knowledge_au AFTER UPDATE ON knowledge_items BEGIN
            INSERT INTO knowledge_fts(knowledge_fts, rowid, title, content, tags)
            VALUES('delete', old.id, old.title, old.content, old.tags);
            INSERT INTO knowledge_fts(rowid, title, content, tags)
            VALUES (new.id, new.title, new.content, new.tags);
        END;
        """
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS knowledge_fts;")
    op.execute("DROP TRIGGER IF EXISTS knowledge_ai;")
    op.execute("DROP TRIGGER IF EXISTS knowledge_ad;")
    op.execute("DROP TRIGGER IF EXISTS knowledge_au;")
    op.drop_index("ix_knowledge_title", table_name="knowledge_items")
    op.drop_table("knowledge_items")
