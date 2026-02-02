# Setup & Installation Guide

## Prerequisites

- **Python 3.10+**: Ensure Python is installed.
- **Poetry**: Dependency manager (`pip install poetry`).
- **Docker & Docker Compose**: For running the PostgreSQL database.

## Installation

1.  **Clone the repository**

    ```bash
    git clone https://github.com/lazza442233/football-analytics.git
    cd football-analytics
    ```

2.  **Install Dependencies**
    This will create a virtual environment and install the `src` package in editable mode.

    ```bash
    poetry install
    ```

3.  **Setup Pre-commit Hooks**
    This ensures that linting (Ruff) and formatting checks run locally before every commit.
    ```bash
    poetry run pre-commit install
    ```

## Database Setup

1.  **Start the Database**
    Use Docker Compose to spin up the Postgres instance.

    ```bash
    docker-compose up -d
    ```

2.  **Configuration**
    Ensure your `.env` file matches the database credentials defined in `docker-compose.yml`.

## Running the Project

### Running Scripts

Always run scripts via `poetry run` to ensure the correct environment and paths are loaded.

```bash
# Example: Ingest Matches
poetry run python -m src.scripts.ingest_matches --comp-id 9 --season-id 281 --events
```

### Running the API

```bash
poetry run uvicorn src.main:app --reload
```
