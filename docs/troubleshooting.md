# Troubleshooting Guide

Common issues and their solutions for the Football Analytics Platform.

---

## Table of Contents

- [Database Connection Errors](#database-connection-errors)
- [Alembic Migration Issues](#alembic-migration-issues)
- [StatsBomb API Issues](#statsbomb-api-issues)
- [Poetry Installation Failures](#poetry-installation-failures)
- [Frontend Build Errors](#frontend-build-errors)
- [ARQ Worker Not Processing Jobs](#arq-worker-not-processing-jobs)
- [Docker Disk Space Issues](#docker-disk-space-issues)
- [Port Already in Use](#port-already-in-use)
- [Import Errors](#import-errors)

---

## Database Connection Errors

### Symptom

```
sqlalchemy.exc.OperationalError: could not connect to server: Connection refused
```

### Solution

```bash
# Check if PostgreSQL is running
docker compose ps postgres

# If not running, start it
docker compose up -d postgres

# Check logs for errors
docker compose logs postgres

# Verify port is not in use
lsof -i :5432

# Test connection manually
poetry run python -c "
from src.database import engine
from sqlalchemy import text
with engine.connect() as conn:
    result = conn.execute(text('SELECT 1'))
    print('✅ Database connected')
"
```

### Still failing?

Check `.env` matches `docker-compose.yml`:

```bash
# .env
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=football_analytics
POSTGRES_HOST=localhost  # "db" in Docker, "localhost" locally

# docker-compose.yml
POSTGRES_USER: postgres
POSTGRES_PASSWORD: postgres
POSTGRES_DB: football_analytics
```

---

## Alembic Migration Issues

### Symptom

```
alembic.util.exc.CommandError: Target database is not up to date.
```

### Solution

```bash
# Check current migration state
poetry run alembic current

# See pending migrations
poetry run alembic heads

# Apply all migrations
poetry run alembic upgrade head

# If migrations are corrupted, reset (⚠️ destroys data)
poetry run alembic downgrade base
poetry run alembic upgrade head
```

### Creating a new migration after model changes

```bash
# 1. Modify src/models.py
# 2. Generate migration
poetry run alembic revision --autogenerate -m "add player nationality column"

# 3. Review generated file in migrations/versions/
# 4. Apply migration
poetry run alembic upgrade head
```

---

## StatsBomb API Issues

### Symptom

```
HTTPError: 403 Forbidden
```

### Solution

StatsBomb Open Data is free but rate-limited. Solutions:

```bash
# 1. Check if you're using the correct endpoint
# Open data uses different base URL than paid accounts

# 2. Clear cache and retry
rm -rf ~/.statsbomb/
poetry run python -m src.scripts.ingest_matches --comp-id 9 --season-id 281

# 3. Add delays between requests (already implemented in statsbombpy)
# If still failing, wait 5 minutes and retry
```

---

## Poetry Installation Failures

### Symptom

```
EnvCommandError: Command failed: python setup.py
```

### Solution

```bash
# Update Poetry
pip install --upgrade poetry

# Clear Poetry cache
poetry cache clear pypi --all

# Reinstall dependencies
rm poetry.lock
poetry install

# If still failing, check Python version
python --version  # Must be 3.12+
```

---

## Frontend Build Errors

### Symptom

```
Error: Cannot find module 'vite'
```

### Solution

```bash
cd frontend

# Clear node_modules
rm -rf node_modules package-lock.json

# Reinstall
npm install

# Verify Node version
node --version  # Must be 18+

# Try with legacy peer deps (if React version conflicts)
npm install --legacy-peer-deps
```

---

## ARQ Worker Not Processing Jobs

### Symptom

Background ingestion jobs remain in "pending" state.

### Solution

```bash
# Check worker is running
docker compose ps worker
# OR if running locally:
ps aux | grep "arq"

# Check worker logs
docker compose logs worker

# Verify Redis connection
redis-cli -h localhost -p 6379 ping
# Should return: PONG

# Restart worker
docker compose restart worker

# Manually enqueue a test job
poetry run python -c "
import asyncio
from src.worker import arq_redis

async def test():
    redis = await arq_redis()
    job = await redis.enqueue_job('test_task')
    print(f'Job ID: {job.job_id}')

asyncio.run(test())
"
```

---

## Docker Disk Space Issues

### Symptom

```
Error response from daemon: no space left on device
```

### Solution

```bash
# Check Docker disk usage
docker system df

# Remove unused images and containers
docker system prune -a

# Remove volumes (⚠️ deletes database data)
docker volume prune

# Restart Docker Desktop (Mac/Windows)
# On Linux, restart Docker daemon:
sudo systemctl restart docker
```

---

## Port Already in Use

### Symptom

```
Error starting userland proxy: listen tcp 0.0.0.0:5432: bind: address already in use
```

### Solution

```bash
# Find process using port
lsof -i :5432  # PostgreSQL
lsof -i :8000  # FastAPI
lsof -i :6379  # Redis

# Kill the process
kill -9 <PID>

# Or change port in docker-compose.yml:
services:
  postgres:
    ports:
      - "5433:5432"  # Use 5433 on host, 5432 in container
```

---

## Import Errors

### Symptom

```python
ModuleNotFoundError: No module named 'src'
```

### Solution

```bash
# Ensure src/ is installed in editable mode
poetry install

# Verify installation
poetry run python -c "import src; print(src.__file__)"

# Always run scripts via poetry run
poetry run python -m src.scripts.ingest_matches  # ✅ Correct
python -m src.scripts.ingest_matches              # ❌ Wrong (uses system Python)
```

---

## Test Failures

### Symptom

```
AssertionError: assert 42 == 43
```

### Common Causes & Solutions

1. **Stale Test Database**

   ```bash
   # Tests create/destroy tables automatically
   # If you suspect corruption, manually drop test DB
   docker compose exec postgres psql -U postgres -c "DROP DATABASE test_football_analytics;"
   poetry run pytest
   ```

2. **Missing Test Data**

   ```bash
   # Some tests require ingested data
   poetry run python -m src.scripts.ingest_matches --comp-id 9 --season-id 281 --events
   poetry run pytest
   ```

3. **Async Test Issues**

   ```bash
   # Ensure pytest-asyncio is installed
   poetry add --group dev pytest-asyncio

   # Check pyproject.toml has:
   # [tool.pytest.ini_options]
   # asyncio_mode = "auto"
   ```

---

## Docker Compose Service Won't Start

### Symptom

```
ERROR: for db  Cannot start service db: driver failed programming external connectivity
```

### Solution

```bash
# Stop all containers
docker compose down

# Remove orphaned containers
docker compose down --remove-orphans

# Rebuild and restart
docker compose up -d --build

# Check logs for specific service
docker compose logs db
docker compose logs api
docker compose logs worker
```

---

## Frontend Can't Connect to API

### Symptom

```
Network Error: Failed to fetch http://localhost:8000/api/players
```

### Solution

1. **Check API is running**

   ```bash
   curl http://localhost:8000/health
   # Should return: {"status": "ok"}
   ```

2. **Check CORS configuration**

   ```python
   # src/main.py
   app.add_middleware(
       CORSMiddleware,
       allow_origins=["http://localhost:5173"],  # Frontend URL
       allow_credentials=True,
       allow_methods=["*"],
       allow_headers=["*"],
   )
   ```

3. **Verify API base URL in frontend**

   ```typescript
   // frontend/src/api/client.ts
   const API_BASE_URL = "http://localhost:8000";  // Should match API port
   ```

---

## Slow Query Performance

### Symptom

Doppelgänger API requests take >5 seconds.

### Solution

```bash
# Check if indexes exist
poetry run python -c "
from src.database import engine
from sqlalchemy import inspect

inspector = inspect(engine)
indexes = inspector.get_indexes('event')
print('Event table indexes:', indexes)
"

# Add missing indexes (create migration)
poetry run alembic revision -m "add event indexes"
```

**Suggested indexes:**

```python
# migrations/versions/xxx_add_event_indexes.py
def upgrade():
    op.create_index('ix_event_player_id', 'event', ['player_id'])
    op.create_index('ix_event_match_id', 'event', ['match_id'])
    op.create_index('ix_event_type', 'event', ['type'])
```

---

## Still Need Help?

If your issue isn't covered here:

1. **Check the logs**
   ```bash
   # Docker logs
   docker compose logs [service_name]

   # Application logs
   tail -f logs/app.log
   ```

2. **Search existing issues**
   - [GitHub Issues](https://github.com/lazza442233/football-analytics/issues)

3. **Create a new issue**
   Include:
   - Operating system and version
   - Python version (`python --version`)
   - Poetry version (`poetry --version`)
   - Docker version (`docker --version`)
   - Full error message and stack trace
   - Steps to reproduce

4. **Ask in Discussions**
   - [GitHub Discussions](https://github.com/lazza442233/football-analytics/discussions)

---

## Debugging Tips

### Enable Debug Logging

```bash
# .env
LOG_LEVEL=DEBUG
JSON_LOGS=false

# Restart services
docker compose restart api worker
```

### Interactive Debugging

```python
# Add breakpoint in code
import pdb; pdb.set_trace()

# Run script in debug mode
poetry run python -m pdb -m src.scripts.ingest_matches --comp-id 9 --season-id 281
```

### Database Query Debugging

```python
# Enable SQLAlchemy query logging
# src/database.py
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=True,  # Prints all SQL queries
)
```

### Redis Queue Inspection

```bash
# Connect to Redis CLI
redis-cli -h localhost -p 6379

# List all keys
KEYS *

# Inspect queue
LRANGE arq:queue 0 -1

# Check job status
HGETALL arq:job:<job_id>
```

---

<p align="center">
  <i>Updated: February 2026</i>
</p>
