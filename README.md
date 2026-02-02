# Football Analytics Platform

A high-performance, asynchronous sports analytics engine designed to ingest, process, and serve modern football data. Built with Python 3.12, FastAPI, and PostgreSQL, leveraging the StatsBomb Open Data dataset.

## 🚀 Features

- **Async-First Architecture**: Fully asynchronous API and Database interactions for high throughput.
- **Data Ingestion Pipeline**: robust ETL scripts to ingest Competitions, Matches, Players, and structured Events from StatsBomb.
- **Modern Database Schema**: SQLModel (SQLAlchemy + Pydantic) ORM with Alembic for migrations.
- **JSONB Storage**: Flexible storage for complex event attributes (xG, pass angles, etc.) using PostgreSQL JSONB types.
- **Containerized**: Fully Dockerized development environment with hot-reloading.

## 🛠 Tech Stack

- **Language**: Python 3.12
- **Web Framework**: [FastAPI](https://fastapi.tiangolo.com/)
- **Database**: PostgreSQL 15 (AsyncPG driver)
- **ORM**: [SQLModel](https://sqlmodel.tiangolo.com/)
- **Migrations**: Alembic (Async configured)
- **Package Manager**: [Poetry](https://python-poetry.org/)
- **Data Source**: [statsbombpy](https://github.com/statsbomb/statsbombpy)

## 📋 Prerequisites

- Docker & Docker Compose
- Python 3.12+ (For local tooling)
- Poetry (`pip install poetry`)

## ⚡️ Getting Started

### 1. Clone & Install Dependencies

```bash
git clone https://github.com/lazza442233/football-analytics.git
cd football-analytics
poetry install
```

### 2. Start Infrastructure

Run the database and API in containers:

```bash
docker compose up -d --build
```

> The API will be available at [http://localhost:8000](http://localhost:8000).
> Interactive Docs: [http://localhost:8000/docs](http://localhost:8000/docs)

### 3. Database Setup (Migrations)

The database starts empty. Apply the schema:

```bash
# Apply migrations to the Dockerized DB from your local machine
# We override POSTGRES_HOST to localhost since Docker maps port 5432
POSTGRES_HOST=localhost poetry run alembic upgrade head
```

### 4. Seed Data (Ingestion)

Ingest data for a specific competition and season using the CLI. For example, to ingest the **2023/2024 Bayer Leverkusen** season (Bundesliga):

```bash
# Bundesliga (Comp ID: 9), Season 2023/2024 (Season ID: 281)
POSTGRES_HOST=localhost poetry run python -m src.scripts.ingest_matches --comp-id 9 --season-id 281
```

To ingest the **2022 Match Data** (World Cup):

```bash
# World Cup (Comp ID: 43), Season 2022 (Season ID: 106)
POSTGRES_HOST=localhost poetry run python -m src.scripts.ingest_matches --comp-id 43 --season-id 106
```

This will:

- Fetch match metadata from StatsBomb.
- Upsert Competition and Match records.
- Ingest Events for all matches in that season.

## 💻 Development Workflow

### Database Migrations

When you modify `src/models.py`, generate a new migration:

```bash
# Generate migration script
POSTGRES_HOST=localhost poetry run alembic revision --autogenerate -m "description_of_change"

# Apply migration
POSTGRES_HOST=localhost poetry run alembic upgrade head
```

### Code Quality

Run the linter and formatter:

```bash
poetry run ruff check .
```

### Testing

Run the test suite (integration tests require the DB running):

```bash
POSTGRES_HOST=localhost poetry run pytest
```

## 📂 Project Structure

```
├── docs/                # Documentation
├── migrations/          # Alembic migration scripts
├── src/                 # Application Source Code
│   ├── api/             # API Routers & Endpoints
│   ├── scripts/         # ETL & Utility Scripts
│   │   ├── ingest_matches.py # CLI for data ingestion
│   │   └── ...
│   ├── services/        # Business Logic & Ingestion
│   ├── config.py        # Environment configuration
│   ├── database.py      # Async DB setup
│   ├── main.py          # FastAPI entry point
│   └── models.py        # SQLModel database schemas
├── tests/               # Pytest suite
├── docker-compose.yml   # Infrastructure definition
└── pyproject.toml       # Dependencies
```
