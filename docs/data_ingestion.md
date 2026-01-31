# Data Ingestion Strategy: StatsBomb Open Data

## Overview

We will ingest event data from the [StatsBomb Open Data](https://github.com/statsbomb/open-data) repository using the `statsbombpy` library.

## Data Hierarchy

StatsBomb organizes data in the following hierarchy:

1.  **Competitions**: (e.g., World Cup, La Liga)
2.  **Matches**: Individual games within a competition.
3.  **Events**: Atomic actions (Pass, Shot, Dribble) within a match.
4.  **Frames** (360 Data): Contextual player locations (available for some matches).

## Schema Mapping Plan

We will iterate on our SQLModel definitions to support this relational structure.

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

## Ingestion Workflow

1.  **ETL Script**: A Python script (`src/ingest.py`) running as a background worker.
2.  **Idempotency**: The script should check if a match has already been ingested before processing it.
3.  **Batch Processing**: We will process one season at a time.
