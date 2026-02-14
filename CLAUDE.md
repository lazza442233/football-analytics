# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a high-performance, asynchronous football analytics platform built with Python 3.12, FastAPI, and PostgreSQL. It ingests and analyzes StatsBomb Open Data, featuring vector-based player similarity search (Doppelgänger Engine) and structured event analytics.

## Essential Commands

### Environment Setup
```bash
# Install dependencies (creates venv and installs src in editable mode)
poetry install

# Start infrastructure (PostgreSQL + Redis + API + Worker)
docker compose up -d

# Setup pre-commit hooks (runs ruff on every commit)
poetry run pre-commit install
```

### Database Operations
```bash
# Run all pending migrations
poetry run alembic upgrade head

# Create a new migration after model changes
poetry run alembic revision --autogenerate -m "description"

# Rollback one migration
poetry run alembic downgrade -1
```

### Data Ingestion
```bash
# Ingest match metadata only (fast)
poetry run python -m src.scripts.ingest_matches --comp-id 9 --season-id 281

# Ingest matches + all event data (slow, comprehensive)
poetry run python -m src.scripts.ingest_matches --comp-id 9 --season-id 281 --events

# Common competition IDs: Bundesliga=9, La Liga=11, World Cup=43
# Season IDs vary (e.g., 281 for 23/24, 106 for 2022 WC)
```

### Code Quality & Testing
```bash
# Run linter and formatter
poetry run ruff check .

# Auto-fix linting issues
poetry run ruff check --fix .

# Run all tests
poetry run pytest

# Run tests with coverage report
poetry run pytest --cov=src --cov-report=term-missing

# Run a single test file
poetry run pytest tests/test_doppelganger.py

# Run a specific test
poetry run pytest tests/test_doppelganger.py::test_function_name
```

### Running Services
```bash
# Start API server (development with hot-reload)
poetry run uvicorn src.main:app --reload

# Start ARQ background worker (for async ingestion tasks)
poetry run arq src.worker.WorkerSettings --watch src
```

## Architecture

### Async-First Design
The entire application is built on async/await. All database operations use AsyncPG, and the API is fully async. Blocking operations (e.g., StatsBomb API calls) are wrapped in `asyncio.to_thread()` to prevent event loop blocking.

### Service Layer Pattern
Business logic lives in `src/services/`, not in routers. The two main services are:
- **StatsBombIngestionService** (`services/ingestion.py`): Handles ETL from StatsBomb API to PostgreSQL
- **AnalyticsService** (`services/analytics.py`): Provides season aggregates and analytics queries

### Background Task Queue (ARQ)
Heavy ingestion jobs are offloaded to an ARQ worker backed by Redis. The worker is defined in `src/worker.py` and runs in a separate container (`docker compose up worker`). This keeps the API responsive during large data loads.

### Database Schema
- **SQLModel** (SQLAlchemy + Pydantic) for ORM with full async support
- **Alembic** for migrations (in `migrations/` directory)
- **JSONB storage** for complex event attributes (xG, pass angles, etc.) in `Event.attributes` column
- Key tables: `Competition`, `Match`, `Player`, `Event`

### The Doppelgänger Engine
A vector-similarity search system for finding players with statistically identical playstyles:

**Architecture:**
- Aggregates `Event` data into `PlayerSeasonStats` (per-90 metrics)
- Transforms stats into vectors using StandardScaler (scikit-learn)
- Uses k-NN with cosine similarity for matching
- Partitioned by position group (GK, DEF, MID, FWD)
- Includes explainability logic (shared strengths, key differences)

**Key Files:**
- `src/analytics/doppelganger/etl.py`: Data extraction and aggregation
- `src/analytics/doppelganger/preprocess.py`: Feature engineering and normalization
- `src/analytics/doppelganger/train.py`: Model training (k-NN)
- `src/analytics/doppelganger/model.py`: Inference and similarity search
- `src/analytics/doppelganger/explain.py`: Match explanations (why two players are similar)
- `src/analytics/doppelganger/config.py`: Feature definitions and thresholds

**Important Concepts:**
- A "vector" represents a `(Player, Season, Position)` tuple
- Harry Kane in 2019 is a different entity than Kane in 2024
- Comparisons respect position groups (you can't compare a goalkeeper to a striker)
- Minimum involvement filter: Players need 180+ minutes to be included
- Similarity threshold: Cosine similarity > 0.70 (distance < 0.30)

## Development Patterns

### Import Structure
The project uses a `src/` layout. Always import from `src.module` (e.g., `from src.models import Player`), never relative imports across packages.

### Testing Patterns
- Use `conftest.py` fixtures for database setup (provides `async_session`)
- Golden Master tests in `test_ingestion_golden_master.py` protect against regression
- Mock external APIs (StatsBomb) using `pytest` mocks
- Async tests are automatically handled via `pytest-asyncio` (configured in `pyproject.toml`)

### Configuration
Environment variables are managed via `src/config.py` using Pydantic Settings. The `.env` file should match credentials in `docker-compose.yml`. Key variables:
- `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`
- `POSTGRES_HOST` (defaults to `localhost`, overridden to `db` in Docker)
- `REDIS_HOST`, `REDIS_PORT`

### Logging
Structured JSON logging is configured in `src/logging_conf.py` using `python-json-logger`. All services use standard `logging.getLogger(__name__)`.

## Common Pitfalls

### Async/Sync Boundaries
When calling blocking code (like `statsbombpy` functions), always wrap in `asyncio.to_thread()`:
```python
# Bad
events = sb.events(match_id=123)

# Good
events = await asyncio.to_thread(sb.events, match_id=123)
```

### Database Sessions
Never store database sessions in instance variables. Always use dependency injection with `get_session()` or create sessions within a context manager:
```python
async with AsyncSession(engine) as session:
    result = await session.execute(select(Player))
```

### Position Mappings
When working with player positions, always use the mappings in `src/analytics/doppelganger/config.py` to convert StatsBomb position names to position groups (GK, DEF, MID, FWD).

### Per-90 Normalization
Any metric that should be normalized per 90 minutes must be added to `NORMALIZE_PER_90_COLS` in the doppelganger config and should end with `_p90` after normalization.

## Documentation References

- **Setup Guide**: `docs/setup_guide.md`
- **Data Ingestion**: `docs/data_ingestion.md`
- **Project Structure**: `docs/project_structure.md`
- **Doppelgänger Spec**: `docs/arch_doppelganger.md`
- **Project Audit**: `docs/audit_feb_2026.md`

## Code Quality Standards

- **Line Length**: 88 characters (Black-compatible)
- **Python Version**: 3.12+
- **Linter**: Ruff with E, F, I rules (errors, pyflakes, import sorting)
- **Pre-commit**: Enforced locally before commits
- **Type Checking**: MyPy configured with Pydantic plugin
- **Test Coverage Target**: 78%+ (current status)
