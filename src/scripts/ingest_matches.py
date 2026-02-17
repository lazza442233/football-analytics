import argparse
import asyncio
import logging

from src.logging_conf import configure_logging
from src.services.ingestion import StatsBombIngestionService

configure_logging()
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(
        description="Ingest matches for a specific Competition and Season."
    )
    parser.add_argument(
        "--comp-id",
        type=int,
        required=True,
        help="Competition ID (e.g., 43 for World Cup)",
    )
    parser.add_argument(
        "--season-id", type=int, required=True, help="Season ID (e.g., 106 for 2022)"
    )
    parser.add_argument(
        "--events",
        action="store_true",
        help="If set, also ingest all events for these matches.",
    )
    parser.add_argument(
        "--parallel",
        type=int,
        default=10,
        help="Number of matches to process in parallel (default: 10)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-ingest already completed matches (default: skip completed)",
    )

    args = parser.parse_args()

    service = StatsBombIngestionService()
    asyncio.run(
        service.ingest_season_matches(
            competition_id=args.comp_id,
            season_id=args.season_id,
            ingest_events=args.events,
            max_concurrency=args.parallel,
            skip_completed=not args.force,
        )
    )


if __name__ == "__main__":
    main()
