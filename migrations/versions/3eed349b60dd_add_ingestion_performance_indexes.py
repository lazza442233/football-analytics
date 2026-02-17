"""add_ingestion_performance_indexes

Revision ID: 3eed349b60dd
Revises: aa6ec71e844a
Create Date: 2026-02-17 10:10:25.599794

"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "3eed349b60dd"
down_revision: Union[str, Sequence[str], None] = "aa6ec71e844a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add indexes for ingestion and analytics query performance."""

    # Event table indexes (largest table, most critical for performance)
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_event_match_id
        ON event(match_id)
    """)

    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_event_player_id
        ON event(player_id)
        WHERE player_id IS NOT NULL
    """)

    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_event_type
        ON event(type)
    """)

    # GIN index for JSONB queries (attributes column)
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_event_attributes_gin
        ON event USING gin(attributes)
    """)

    # Match table indexes
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_match_comp_season
        ON match(competition_id, season_id)
    """)

    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_match_date
        ON match(match_date)
    """)

    # Player table - GIN index for fuzzy name search
    # First ensure pg_trgm extension exists
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")

    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_player_name_gin
        ON player USING gin(name gin_trgm_ops)
    """)


def downgrade() -> None:
    """Remove indexes."""
    op.execute("DROP INDEX IF EXISTS idx_event_match_id")
    op.execute("DROP INDEX IF EXISTS idx_event_player_id")
    op.execute("DROP INDEX IF EXISTS idx_event_type")
    op.execute("DROP INDEX IF EXISTS idx_event_attributes_gin")
    op.execute("DROP INDEX IF EXISTS idx_match_comp_season")
    op.execute("DROP INDEX IF EXISTS idx_match_date")
    op.execute("DROP INDEX IF EXISTS idx_player_name_gin")
    # Note: Not dropping pg_trgm extension as other parts of system may use it
