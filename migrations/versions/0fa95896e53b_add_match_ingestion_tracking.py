"""add_match_ingestion_tracking

Revision ID: 0fa95896e53b
Revises: 3eed349b60dd
Create Date: 2026-02-17 10:10:44.807963

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0fa95896e53b"
down_revision: Union[str, Sequence[str], None] = "3eed349b60dd"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add timestamp column to track when match events were ingested."""

    # Add nullable timestamp column
    op.add_column(
        "match", sa.Column("events_ingested_at", sa.TIMESTAMP(), nullable=True)
    )

    # Create partial index for efficient queries of pending matches
    # Only indexes rows where events_ingested_at IS NULL
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_match_ingestion_status
        ON match(events_ingested_at)
        WHERE events_ingested_at IS NULL
    """)


def downgrade() -> None:
    """Remove ingestion tracking column and index."""
    op.execute("DROP INDEX IF EXISTS idx_match_ingestion_status")
    op.drop_column("match", "events_ingested_at")
