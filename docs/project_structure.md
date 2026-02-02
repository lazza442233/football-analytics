# Project Structure

This document outlines the organization of the codebase, located primarily in the `src/` directory.

## Architecture Pattern

We utilize a **Source Layout** (`src/`) pattern. This treats the application code as an installable Python package, preventing import errors and enforcing clear boundaries between the application logic and the runtime scripts.

## Directory Layout

```
src/
├── api/                  # FastAPI Application
│   └── routers/          # API Endpoints (Players, Matches, etc.)
│
├── scripts/              # Data Ingestion & Utility Scripts
│   ├── ingest_matches.py # CLI Tool for ingesting competition data
│   └── research_statsbomb.py # Development utilities
│
├── services/             # Business Logic Layer
│   └── ingestion.py      # Core logic for processing StatsBomb data
│
├── config.py             # Configuration (Env vars)
├── database.py           # Database connection & Session management
├── main.py               # Application Entrypoint
└── models.py             # SQLModel Database Entities
```

## Key Components

### 1. Services (`src/services/`)

Encapsulates complex business logic.

- **IngestionService**: Responsible for orchestrating the fetch-transform-load process for StatsBomb data. It handles relational integrity (creating Players before Events) and transaction management.

### 2. Scripts (`src/scripts/`)

Executable modules for operational tasks.

- **`ingest_matches.py`**: The primary CLI entry point for populating the database with historical match data. Arguments: `--comp-id`, `--season-id`.

### 3. API (`src/api/`)

The REST interface for the data.

- Uses `APIRouter` to modularize endpoints.
- Currently serves basic entity retrieval (Players).

### 4. Database Layer

- **`models.py`**: Defines the schema. Tables are created automatically via Alembic migrations (managed externally in root).
- **`database.py`**: Provides the `get_session` dependency for async database access.
