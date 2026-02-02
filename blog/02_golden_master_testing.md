# The Golden Master: Testing Data Integrity in Sports Analytics

_Date: February 2nd, 2026_

In [Article 1](./01_why_async_fastapi.md), I discussed using **PostgreSQL JSONB** to store the messy, semi-structured nature of football events (passes, shots, pressures). While flexible, this approach creates a new engineering challenge: **Regression Testing**.

If I modify my ingestion logic to optimize performance, how do I guarantee I haven't accidentally stopped capturing the `angle` of a pass or the `outcome` of a dribble?

## The Problem: Unit Tests Aren't Enough

Standard unit tests usually check small functions in isolation:

> _"Does the `parse_date` function return a datetime?"_

But in an ETL (Extract, Transform, Load) pipeline, we need to ensure that a massive nested JSON payload from the API translates into the **exact** correct database row. Writing individual assertions for 200+ event types is impossible.

## The Solution: Golden Master Testing

I implemented a **Golden Master** (or Snapshot) testing strategy. The concept is simple:

1.  **Capture Input**: Save a raw response from the StatsBomb API as a generic fixture (e.g., `mock_events.json`).
2.  **Define Expected Output**: Manually inspect and verify the resulting database row for a specific, complex event. This becomes the "Golden Master".
3.  **The Test**:
    - Spin up a test database.
    - Mock the API client to return the fixture.
    - Run the **actual** full ingestion pipeline.
    - Assert that the database row matches the Golden Master **exactly**.

### The Code

Here is a simplified view of our test:

```python
async def test_ingestion_golden_master(session: AsyncSession):
    # 1. Setup Mock
    mock_events = load_json("tests/fixtures/golden_master_events.json")

    with patch("statsbombpy.sb.events", return_value=mock_events):
        # 2. Run Ingestion (The real code)
        await ingest_match(session, match_id=123)

    # 3. Verify specifically complex attributes
    stmt = select(Event).where(Event.type == "Pass")
    result = await session.execute(stmt)
    pass_event = result.scalars().first()

    # The Golden Assertion
    assert pass_event.attributes["pass"]["angle"] == 2.14
    assert pass_event.attributes["pass"]["recipient"]["name"] == "Granit Xhaka"
```

## Why This Matters

This test gave me the confidence to completely refactor the `ingestion.py` service. I pulled out helper functions and dry-ed up the code, knowing that if I broke the JSON mapping, the Golden Master would fail immediately.

In a data project, **integrity is everything**. If you can't trust your historical data, you can't trust your future models.
