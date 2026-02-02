import asyncio

from src.services.ingestion import StatsBombIngestionService

if __name__ == "__main__":
    service = StatsBombIngestionService()
    asyncio.run(service.run())
