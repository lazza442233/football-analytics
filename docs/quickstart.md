# Quick Start Guide

Get up and running with the Football Analytics Platform in 10 minutes.

---

## What You'll Learn

By the end of this guide, you'll have:

- ✅ A running Football Analytics Platform
- ✅ Ingested real StatsBomb match data
- ✅ Executed your first player similarity search
- ✅ Viewed results in the React dashboard

---

## Prerequisites

Before starting, ensure you have:

- **Docker & Docker Compose** (for infrastructure)
- **Python 3.12+** (check with `python --version`)
- **Poetry** (install via `pip install poetry`)
- **10 GB free disk space** (for database and dependencies)

---

## Step 1: Clone & Install (2 minutes)

```bash
# Clone the repository
git clone https://github.com/lazza442233/football-analytics.git
cd football-analytics

# Install Python dependencies
poetry install

# This creates a virtual environment and installs all packages
# Expected output: "Installing dependencies from lock file... (47 packages)"
```

**Verify installation:**

```bash
poetry run python -c "from src.models import Player; print('✅ Installation successful')"
```

---

## Step 2: Start Infrastructure (3 minutes)

```bash
# Start PostgreSQL and Redis
docker compose up -d postgres redis

# Wait for PostgreSQL to be ready
sleep 5

# Run database migrations
poetry run alembic upgrade head
```

**Verify infrastructure:**

```bash
# Check containers are running
docker compose ps

# Expected output:
# NAME      STATUS   PORTS
# postgres  Up       0.0.0.0:5432->5432/tcp
# redis     Up       0.0.0.0:6379->6379/tcp
```

---

## Step 3: Ingest Sample Data (5 minutes)

Let's load the 2022 FIFA World Cup dataset:

```bash
poetry run python -m src.scripts.ingest_matches \
  --comp-id 43 \
  --season-id 106 \
  --events
```

**What's happening:**

- Fetching 64 World Cup matches from StatsBomb API
- Storing ~200,000 events (passes, shots, tackles)
- Creating player profiles for ~800 players

**Progress output:**

```
INFO:src.services.ingestion:Ingesting competition_id=43, season_id=106
INFO:src.services.ingestion:Found 64 matches
INFO:src.services.ingestion:Match 1/64: Argentina vs Saudi Arabia
INFO:src.services.ingestion:  - Created 22 players
INFO:src.services.ingestion:  - Ingested 3,482 events
...
INFO:src.services.ingestion:✅ Ingestion complete! Total: 64 matches, 211,394 events
```

---

## Step 4: Start the API (1 minute)

Open a new terminal and start the FastAPI server:

```bash
poetry run uvicorn src.main:app --reload
```

**Verify API is running:**

```bash
curl http://localhost:8000/health

# Expected output:
# {"status": "healthy", "timestamp": "2026-02-14T..."}
```

Visit the interactive API docs: **http://localhost:8000/docs**

---

## Step 5: Search for Similar Players

### Option A: Using the API Docs (GUI)

1. Navigate to http://localhost:8000/docs
2. Find the `/analytics/doppelganger` endpoint
3. Click "Try it out"
4. Enter parameters:
   - `player_id`: 5503 (Lionel Messi)
   - `season_id`: 106 (2022 World Cup)
   - `limit`: 5
5. Click "Execute"

**Expected response:**

```json
{
  "target": {
    "player_id": 5503,
    "name": "Lionel Messi",
    "season": "2022",
    "position_group": "FWD"
  },
  "similar_players": [
    {
      "player_id": 3089,
      "name": "Kylian Mbappé",
      "similarity_score": 0.94,
      "explanation": {
        "shared_strengths": [
          "High xG per 90 (>0.8)",
          "Progressive carries"
        ],
        "key_difference": "Mbappé averages +2.1 more dribbles per 90"
      }
    }
    // ... 4 more matches
  ]
}
```

### Option B: Using curl

```bash
curl "http://localhost:8000/analytics/doppelganger?player_id=5503&season_id=106&limit=5"
```

### Option C: Using Python

```python
import requests

response = requests.get(
    "http://localhost:8000/analytics/doppelganger",
    params={
        "player_id": 5503,  # Messi
        "season_id": 106,   # 2022 World Cup
        "limit": 5
    }
)

data = response.json()
print(f"Target: {data['target']['name']}")
print(f"Similar players:")
for match in data['similar_players']:
    print(f"  - {match['name']}: {match['similarity_score']:.2f}")
```

---

## Step 6: Launch the Frontend (Optional)

Open a new terminal:

```bash
cd frontend

# Install dependencies
npm install

# Start dev server
npm run dev
```

Visit **http://localhost:5173** to use the React dashboard.

**Features:**

- 🔍 Player search with autocomplete
- 📊 Radar charts comparing player profiles
- 📈 Per-90 statistics visualization
- 🎯 Similarity explanations

---

## What's Next?

### Explore More Data

Ingest additional competitions:

```bash
# Bundesliga 2023/24
poetry run python -m src.scripts.ingest_matches --comp-id 9 --season-id 281 --events

# La Liga 2022/23
poetry run python -m src.scripts.ingest_matches --comp-id 11 --season-id 90 --events

# Premier League 2021/22
poetry run python -m src.scripts.ingest_matches --comp-id 2 --season-id 42 --events
```

### Try Different Players

Find the player ID for your favorite player:

```bash
# Search the database
poetry run python -c "
from src.database import engine
from src.models import Player
from sqlalchemy import select

with engine.connect() as conn:
    result = conn.execute(
        select(Player).where(Player.name.ilike('%ronaldo%'))
    )
    for player in result:
        print(f'{player.id}: {player.name}')
"
```

### Understand the Architecture

- [Doppelgänger Architecture](dev/arch_doppelganger.md) - How the similarity engine works
- [Project Structure](project_structure.md) - Codebase organization
- [API Reference](http://localhost:8000/docs) - Full endpoint documentation

### Run Tests

```bash
# Run the test suite
poetry run pytest

# With coverage report
poetry run pytest --cov=src
```

---

## Common Issues

### Database Connection Failed

```bash
# Check if PostgreSQL is running
docker compose ps postgres

# Restart if needed
docker compose restart postgres

# Verify connection
poetry run python -c "from src.database import engine; engine.connect()"
```

### Port Already in Use

```bash
# Find process using port 8000
lsof -i :8000

# Kill the process
kill -9 <PID>
```

### StatsBomb API Rate Limit

```bash
# Clear cache and retry
rm -rf ~/.statsbomb/
```

**Full troubleshooting guide**: [docs/troubleshooting.md](troubleshooting.md)

---

## Stopping the Application

```bash
# Stop API (Ctrl+C in the terminal)

# Stop infrastructure
docker compose down

# Remove volumes (⚠️ deletes database data)
docker compose down -v
```

---

## Summary

You've successfully:

- ✅ Installed the Football Analytics Platform
- ✅ Ingested real match data (2022 World Cup)
- ✅ Found players similar to Lionel Messi
- ✅ Explored the API documentation

**Next steps:**

- Experiment with different players and competitions
- Read the [Architecture Guide](dev/arch_doppelganger.md)
- Contribute a new feature ([CONTRIBUTING.md](../CONTRIBUTING.md))

---

## Need Help?

- 📖 **Documentation**: [docs/](.)
- 🐛 **Bug Reports**: [GitHub Issues](https://github.com/lazza442233/football-analytics/issues)
- 💬 **Questions**: [GitHub Discussions](https://github.com/lazza442233/football-analytics/discussions)

---

<p align="center">
  <i>Happy analyzing! ⚽📊</i>
</p>
