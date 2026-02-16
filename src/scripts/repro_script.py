import asyncio
import sys

from src.analytics.doppelganger import schemas, service
from src.analytics.doppelganger.registry import registry
from src.database import get_session

# Add src to path if needed (might not be needed inside container if installed)
sys.path.append("/app")


async def reproduce():
    # We need a session
    # HACK: Create session generator and get one
    async for session in get_session():
        print("Got session")
        # Initialize service
        svc = service.DoppelgangerService(session)

        # Construct query
        query = schemas.DoppelgangerQuery(player_id=10955, season_id=282, limit=10)

        try:
            print(
                f"Searching for player {query.player_id}, season {query.season_id}..."
            )
            # Check registry status
            status = registry.status
            print(f"Registry status: {status}")

            result = await svc.search_similar_players(query)
            print("Success!")
            print(result)
        except Exception:
            print("CRASHED:")
            import traceback

            traceback.print_exc()
        finally:
            # Clean up if needed, though session context manager
            # handles commit/rollback usually
            pass
        break  # Only need one session


if __name__ == "__main__":
    asyncio.run(reproduce())
