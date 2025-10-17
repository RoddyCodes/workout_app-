"""create workout_templates table (initial)

Revision ID: 0001_create_workout_templates
Revises:
Create Date: 2025-10-16
"""
from __future__ import annotations
# isort: skip_file

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "0001_create_workout_templates"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # workout_templates table only; feedback exists from app create_all in dev
    op.create_table(
        "workout_templates",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("goal", sa.String(length=64), nullable=False),
        sa.Column("experience_level", sa.String(length=32), nullable=False),
        sa.Column("payload", sa.Text(), nullable=False),
    )
    op.create_index("ix_workout_templates_name", "workout_templates", ["name"], unique=False)
    op.create_index("ix_workout_templates_goal", "workout_templates", ["goal"], unique=False)
    op.create_index(
        "ix_workout_templates_experience_level",
        "workout_templates",
        ["experience_level"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_table("workout_templates")
