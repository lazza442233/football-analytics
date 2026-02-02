# Football Analytics Platform

A high-performance, asynchronous sports analytics engine designed to ingest, process, and serve modern football data. Built with Python 3.12, FastAPI, and PostgreSQL, leveraging the StatsBomb Open Data dataset.

## 🚀 Features

- **Async-First Architecture**: Fully asynchronous API and Database interactions for high throughput.
- **Background Workers**: Heavy ingestion tasks are offloaded to an asynchronous job queue (ARQ/Redis) to ensure API responsiveness.
- **Data Ingestion Pipeline**: robust ETL scripts to ingest Competitions, Matches, Players, and structured Events from StatsBomb.
- **Modern Database Schema**: SQLModel (SQLAlchemy + Pydantic) ORM with Alembic for migrations.
- **JSONB Storage**: Flexible storage for complex event attributes (xG, pass angles, etc.) using PostgreSQL JSONB types.
- **Search & Analytics**:
  - Full-text search usage of `Match` events.
  - Granular event filtering (e.g., "Passes in the final third").
  - **Season Aggregates**: Aggregate stats for players across an entire season (Pass Completion, xG, etc.).
- **Containerized**: Fully Dockerized development environment with hot-reloading.

## 🛠 Tech Stack

- **Language**: Python 3.12
- **Web Framework**: [FastAPI](https://fastapi.tiangolo.com/)
- **Database**: PostgreSQL 15 (AsyncPG driver)
- **ORM**: [SQLModel](https://sqlmodel.tiangolo.com/)
- **Task Queue**: [ARQ](https://arq-docs.helpmanual.io/) with Redis
- **Migrations**: Alembic (Async configured)
- **Package Manager**: [Poetry](https://python-poetry.org/)
- **Data Source**: [statsbombpy](https://github.com/statsbomb/statsbombpy)

## 📋 Prerequisites

- Docker & Docker Compose
- Python 3.12+ (For local tooling)
- Poetry (`pip install poetry`)

## ⚡️ Getting Started

For a complete guide on setting up the environment, database, and dependencies, please refer to the [**Setup & Installation Guide**](docs/setup_guide.md).

### Quick Start

1.  **Start Infrastructure**: `docker compose up -d`
2.  **Install Application**: `poetry install` (Installs `src` in editable mode)
3.  **Run Migrations**: `poetry run alembic upgrade head`

### Data Ingestion

Use the CLI to ingest matches and event data from StatsBomb.

```bash
# Example: Ingest Bundesliga 23/24 (Matches + Events)
poetry run python -m src.scripts.ingest_matches --comp-id 9 --season-id 281 --events
```

👉 **[See Data Ingestion Docs](docs/data_ingestion.md)** for detailed usage, flags, and available competitions.

## 💻 Development Workflow

### Code Quality & Testing

We enforce strict standards using `ruff` and `pytest`.

```bash
# Run Linter & Formatter
poetry run ruff check .

# Run Tests
poetry run pytest
```

## 📂 Project Structure

We follow a `src`-layout pattern to ensure proper packaging and import behavior.

```
src/
├── api/          # REST API (Routers for Matches, Players, Analytics)
├── scripts/      # ETL CLI Tools
├── services/     # Business Logic (Ingestion, Analysis)
├── models.py     # Database Schema (SQLModel)
└── ...
```

👉 **[Full Project Structure Documentation](docs/project_structure.md)**
