"""add unaccent extension

Revision ID: aa6ec71e844a
Revises: fe09d0572b96
Create Date: 2026-02-14 15:45:34.420809

"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "aa6ec71e844a"
down_revision: Union[str, Sequence[str], None] = "fe09d0572b96"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("CREATE EXTENSION IF NOT EXISTS unaccent;")


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("DROP EXTENSION IF EXISTS unaccent;")
