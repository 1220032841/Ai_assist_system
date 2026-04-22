"""add assignment language and template fields

Revision ID: d4c2f8b91c21
Revises: b1d5d4f0c0a2
Create Date: 2026-04-22 17:30:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "d4c2f8b91c21"
down_revision: Union[str, None] = "b1d5d4f0c0a2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TABLE assignments ADD COLUMN IF NOT EXISTS language VARCHAR")
    op.execute("ALTER TABLE assignments ADD COLUMN IF NOT EXISTS starter_code TEXT")
    op.execute("ALTER TABLE assignments ADD COLUMN IF NOT EXISTS example_input TEXT")
    op.execute("ALTER TABLE assignments ADD COLUMN IF NOT EXISTS example_output TEXT")
    op.execute("UPDATE assignments SET language = 'cpp' WHERE language IS NULL OR language = ''")
    op.execute("ALTER TABLE assignments ALTER COLUMN language SET DEFAULT 'cpp'")
    op.execute("ALTER TABLE assignments ALTER COLUMN language SET NOT NULL")


def downgrade() -> None:
    op.execute("ALTER TABLE assignments DROP COLUMN IF EXISTS example_output")
    op.execute("ALTER TABLE assignments DROP COLUMN IF EXISTS example_input")
    op.execute("ALTER TABLE assignments DROP COLUMN IF EXISTS starter_code")
    op.execute("ALTER TABLE assignments DROP COLUMN IF EXISTS language")