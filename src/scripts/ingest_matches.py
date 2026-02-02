import argparse
import asyncio
import logging
from src.services.ingestion import StatsBombIngestionService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(
        description="Ingest matches for a specific Competition and Season.")
    parser.add_argument("--comp-id", type=int, required=True,
                        help="Competition ID (e.g., 43 for World Cup)")
    parser.add_argument("--season-id", type=int, required=True,
                        help="Season ID (e.g., 106 for 2022)")

    args = parser.parse_args()

    service = StatsBombIngestionService()
    asyncio.run(service.ingest_season_matches(
        competition_id=args.comp_id,
        season_id=args.season_id
    ))


if __name__ == "__main__":
    main()
