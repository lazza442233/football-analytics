# Setup & Installation Guide

This guide will help you set up the Football Analytics Platform for both **running the application** (Docker-based) and **active development** (Poetry-based).

---

## 🎯 Choose Your Path

- **🚀 I just want to run it** → [Quick Start (Docker)](#quick-start-docker)
- **💻 I want to develop/test** → [Development Setup](#development-setup)
- **🐛 Something's broken** → [Troubleshooting](troubleshooting.md)

---

## Quick Start (Docker)

### Prerequisites

- Docker Engine 20.10+
- Docker Compose 2.0+
- 4GB RAM available for containers

### Installation (5 minutes)

1. **Clone the repository**

   ```bash
   git clone https://github.com/lazza442233/football-analytics.git
   cd football-analytics
   ```

2. **Configure environment**

   ```bash
   cp .env.example .env
   # The default values work out-of-the-box with docker-compose.yml
   ```

3. **Start all services**

   ```bash
   docker compose up -d
   ```

   This starts:
   - PostgreSQL (port 5432)
   - Redis (port 6379)
   - FastAPI (port 8000)
   - ARQ Worker (background)
   - Frontend (port 5173)

4. **Verify installation**

   ```bash
   # Check all containers are running
   docker compose ps

   # Expected output:
   # NAME                STATUS          PORTS
   # postgres            Up             0.0.0.0:5432->5432/tcp
   # redis               Up             0.0.0.0:6379->6379/tcp
   # api                 Up             0.0.0.0:8000->8000/tcp
   # worker              Up
   # frontend            Up             0.0.0.0:5173->5173/tcp
   ```

5. **Access the application**

   - Frontend: http://localhost:5173
   - API Docs: http://localhost:8000/docs
   - Database: `postgresql://postgres:postgres@localhost:5432/football_analytics`

**🎉 You're ready!** Skip to [Data Ingestion](#data-ingestion) to load sample data.

---

## Development Setup

For active development with hot-reloading, testing, and linting.

### Prerequisites

- **Python 3.12+**: Check with `python --version`
- **Poetry**: Install via `pip install poetry`
- **Docker Compose**: For infrastructure only (PostgreSQL + Redis)
- **Node.js 18+**: For frontend development

### Step 1: Install Python Dependencies

```bash
# Create virtual environment and install packages
poetry install

# Verify installation
poetry run python -c "from src.models import Player; print('✅ Imports working')"
```

**What this does:**
- Creates an isolated virtual environment in `.venv/`
- Installs FastAPI, SQLModel, pytest, and all dependencies
- Installs `src/` as an editable package (allows `from src.models import ...`)

### Step 2: Start Infrastructure

```bash
# Start only PostgreSQL and Redis (no API or worker)
docker compose up -d postgres redis

# Wait for PostgreSQL to be ready (~5 seconds)
docker compose logs postgres | grep "ready to accept connections"
```

### Step 3: Run Database Migrations

```bash
# Apply all pending migrations
poetry run alembic upgrade head

# Verify tables were created
poetry run python -c "
from src.database import engine
from sqlalchemy import inspect
inspector = inspect(engine)
print(inspector.get_table_names())
"
```

### Step 4: Setup Development Tools

```bash
# Install pre-commit hooks (runs ruff on every commit)
poetry run pre-commit install

# Verify pre-commit works
poetry run pre-commit run --all-files
```

### Step 5: Run the Application Locally

**Terminal 1: API Server**

```bash
poetry run uvicorn src.main:app --reload --port 8000
```

**Terminal 2: Background Worker**

```bash
poetry run arq src.worker.WorkerSettings --watch src
```

**Terminal 3: Frontend Dev Server**

```bash
cd frontend
npm install
npm run dev
```

**✅ Development environment ready!**

- API: http://localhost:8000
- Frontend: http://localhost:5173
- Hot-reload enabled for both backend and frontend

---

## Data Ingestion

### Quick Test: Ingest a Single Season

```bash
# Bundesliga 2023/24 (9 = Bundesliga, 281 = Season 23/24)
poetry run python -m src.scripts.ingest_matches \
  --comp-id 9 \
  --season-id 281 \
  --events

# This will:
# 1. Fetch ~300 matches from StatsBomb API
# 2. Store match metadata (teams, scores, dates)
# 3. Ingest ~500,000 events (passes, shots, tackles)
# 4. Extract player statistics
#
# Time: ~5-10 minutes depending on network speed
```

### Available Competitions

| Competition        | ID  | Recent Season IDs          |
|--------------------|-----|----------------------------|
| Bundesliga         | 9   | 281 (23/24)                |
| La Liga            | 11  | 90 (22/23), 281 (23/24)    |
| Premier League     | 2   | 42 (21/22)                 |
| FIFA World Cup     | 43  | 106 (2022)                 |
| Champions League   | 16  | Various                    |

**Find all competitions:**

```bash
poetry run python -c "
from statsbombpy import sb
comps = sb.competitions()
print(comps[['competition_id', 'competition_name', 'season_id', 'season_name']])
"
```

### Ingestion Options

```bash
# Metadata only (fast, useful for development)
poetry run python -m src.scripts.ingest_matches --comp-id 9 --season-id 281

# Full ingestion (matches + events)
poetry run python -m src.scripts.ingest_matches --comp-id 9 --season-id 281 --events

# Multiple seasons (run sequentially)
for season in 27 37 42; do
  poetry run python -m src.scripts.ingest_matches --comp-id 2 --season-id $season --events
done
```

---

## Running Tests

### Basic Test Execution

```bash
# Run all tests
poetry run pytest

# Run with output
poetry run pytest -v

# Run a specific test file
poetry run pytest tests/analytics/test_doppelganger.py

# Run a specific test
poetry run pytest tests/analytics/test_doppelganger.py::test_find_similar_players
```

### Coverage Reports

```bash
# Generate coverage report
poetry run pytest --cov=src --cov-report=term-missing

# Generate HTML report
poetry run pytest --cov=src --cov-report=html
open htmlcov/index.html
```

### Test Database

Tests automatically use a separate test database:

```python
# conftest.py creates an isolated async session
@pytest.fixture
async def async_session():
    # Creates temporary tables
    # Rolls back after each test
    # No pollution of development data
```

---

## Code Quality Standards

### Linting with Ruff

```bash
# Check for errors
poetry run ruff check .

# Auto-fix safe issues
poetry run ruff check --fix .

# Check specific files
poetry run ruff check src/analytics/
```

### Type Checking with MyPy

```bash
# Run type checker
poetry run mypy src/

# Ignore specific errors (use sparingly)
# type: ignore[error-code]
```

### Pre-commit Hooks

Automatically runs before every commit:

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format
```

**Override (not recommended):**

```bash
git commit --no-verify -m "emergency fix"
```

---

## Environment Variables Reference

### Core Configuration

```bash
# .env
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=football_analytics
POSTGRES_HOST=localhost  # "db" when running API in Docker
POSTGRES_PORT=5432

REDIS_HOST=localhost  # "redis" when running worker in Docker
REDIS_PORT=6379

# Optional: Logging
LOG_LEVEL=INFO  # DEBUG | INFO | WARNING | ERROR
JSON_LOGS=false  # Set to "true" for production

# Optional: API Configuration
API_HOST=0.0.0.0
API_PORT=8000
CORS_ORIGINS=http://localhost:5173,http://localhost:3000
```

### Docker-Specific Overrides

When running services in Docker, override hostnames:

```yaml
# docker-compose.yml
environment:
  POSTGRES_HOST: db  # Container name, not "localhost"
  REDIS_HOST: redis
```

---

## Next Steps

- **Load Data**: See [Data Ingestion Guide](data_ingestion.md)
- **Explore API**: Visit http://localhost:8000/docs
- **Understand Architecture**: Read [Doppelgänger Spec](dev/arch_doppelganger.md)
- **Having Issues?**: Check [Troubleshooting Guide](troubleshooting.md)

---

## Need Help?

- 🐛 **Bug Report**: [GitHub Issues](https://github.com/lazza442233/football-analytics/issues)
- 💬 **Questions**: [GitHub Discussions](https://github.com/lazza442233/football-analytics/discussions)
- 📖 **Documentation**: [docs/](.)
