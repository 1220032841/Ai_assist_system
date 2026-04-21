"""add class_groups table

Revision ID: b1d5d4f0c0a2
Revises: 9d9b7f3f2a11
Create Date: 2026-04-09 00:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "b1d5d4f0c0a2"
down_revision: Union[str, None] = "9d9b7f3f2a11"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS class_groups (
            id SERIAL PRIMARY KEY,
            name VARCHAR NOT NULL UNIQUE,
            created_at TIMESTAMPTZ DEFAULT now()
        )
        """
    )
    op.execute("CREATE INDEX IF NOT EXISTS ix_class_groups_id ON class_groups (id)")
    op.execute("CREATE UNIQUE INDEX IF NOT EXISTS ix_class_groups_name ON class_groups (name)")


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_class_groups_name")
    op.execute("DROP INDEX IF EXISTS ix_class_groups_id")
    op.execute("DROP TABLE IF EXISTS class_groups")
