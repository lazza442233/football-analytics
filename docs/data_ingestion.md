# Data Ingestion Strategy: StatsBomb Open Data

## Overview

We will ingest event data from the [StatsBomb Open Data](https://github.com/statsbomb/open-data) repository using the `statsbombpy` library.

## Data Hierarchy

StatsBomb organizes data in the following hierarchy:

1.  **Competitions**: (e.g., World Cup, La Liga)
2.  **Matches**: Individual games within a competition.
3.  **Events**: Atomic actions (Pass, Shot, Dribble) within a match.
4.  **Frames** (360 Data): Contextual player locations (available for some matches).

## Current Schema Architecture

We use **SQLModel** to define our database schema, ensuring strict typing and automatic migration generation.

### 1. `Competition` Table

| StatsBomb Field     | Our DB Column | Type         |
| :------------------ | :------------ | :----------- |
| `competition_id`    | `id`          | Integer (PK) |
| `competition_name`  | `name`        | String       |
| `competiton_gender` | `gender`      | String       |

### 2. `Match` Table

| StatsBomb Field            | Our DB Column    | Type         |
| :------------------------- | :--------------- | :----------- |
| `match_id`                 | `id`             | Integer (PK) |
| `competition_id`           | `competition_id` | Integer (FK) |
| `match_date`               | `date`           | DateTime     |
| `home_team.home_team_name` | `home_team`      | String       |
| `away_team.away_team_name` | `away_team`      | String       |
| `home_score`               | `home_score`     | Integer      |
| `away_score`               | `away_score`     | Integer      |

### 3. `Player` Table (Refined)

We currently have a simple `Player` table. We needs to align IDs.
| StatsBomb Field | Our DB Column | Type |
| :--- | :--- | :--- |
| `player_id` | `id` | Integer (PK) |
| `player_name` | `name` | String |
| (Derived) | `current_team_id` | Integer (FK) |

### 4. `Event` Table (The "Big Data")

Events have common fields and type-specific fields. We might use a JSONB column for the generic attributes to keep the schema flexible.

| StatsBomb Field   | Our DB Column | Type         |
| :---------------- | :------------ | :----------- |
| `id` (UUID)       | `id`          | UUID (PK)    |
| `match_id`        | `match_id`    | Integer (FK) |
| `minute`          | `minute`      | Integer      |
| `second`          | `second`      | Integer      |
| `type.name`       | `type`        | String       |
| `player.id`       | `player_id`   | Integer (FK) |
| `team.id`         | `team_id`     | Integer (FK) |
| `location`        | `location_x`  | Float        |
| `location`        | `location_y`  | Float        |
| (Everything else) | `attributes`  | JSONB        |

## Ingestion Scripts

We have refactored ingestion logic into specific scripts located in `src/scripts/`.

### 1. Ingest Matches (Bulk Metadata)

**Script**: `src/scripts/ingest_matches.py`

This script fetches competition info and all available matches for that competition/season. It upserts `Competition` and `Match` records into the database.

**Usage**:

```bash
# Needs ENV vars if not set in .env
PYTHONPATH=. POSTGRES_HOST=localhost poetry run python src/scripts/ingest_matches.py
```

_Note: Currently hardcoded to World Cup 2022 inside the script. Future parameterization planned._

### 2. Ingest Detailed Data (Service Based)

**Script**: `src/scripts/ingest_data.py`

This script utilizes the `StatsBombIngestionService` to perform a deep fetch of events. Currently tailored for specific teams (e.g., Bayer Leverkusen) to test complex relational data ingestion (Events, Players).

**Usage**:

```bash
PYTHONPATH=. POSTGRES_HOST=localhost poetry run python src/scripts/ingest_data.py
```

### 3. Exploratory Research

**Script**: `src/scripts/research_statsbomb.py`

A utility script to inspect the raw DataFrames returned by `statsbombpy` without writing to the database. Useful for debugging schema changes.

## Workflow

1.  **Run Migrations**: Ensure DB schema is up to date (`alembic upgrade head`).
2.  **Fetch Metadata**: Run `ingest_matches.py` to populate the `match` table.
3.  **Ingest Events**: (Coming Soon) Run event-level ingestion for specific match IDs.
