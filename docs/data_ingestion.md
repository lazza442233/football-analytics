# Data Ingestion Strategy: StatsBomb Open Data

## Overview

We will ingest event data from the [StatsBomb Open Data](https://github.com/statsbomb/open-data) repository using the `statsbombpy` library.

## Usage (CLI)

The project includes a robust CLI tool for ingesting data by Competition and Season.

```bash
# General Syntax
python -m src.scripts.ingest_matches --comp-id <ID> --season-id <ID>
```

### Common Competition IDs

| Competition | Comp ID | Season 2023/24 ID | Season 2022 ID (WC) |
| :---------- | :------ | :---------------- | :------------------ |
| Bundesliga  | 9       | 281               | N/A                 |
| World Cup   | 43      | N/A               | 106                 |
| La Liga     | 11      | 281               | -                   |

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

### 3. `Player` Table

| StatsBomb Field | Our DB Column | Type         |
| :-------------- | :------------ | :----------- |
| `player_id`     | `id`          | Integer (PK) |
| `player_name`   | `name`        | String       |
| `position.name` | `position`    | String       |

### 4. `Event` Table (The "Big Data")

Events are stored with core metadata in columns and complex attributes (xG, coordinates, pass end location) in a **JSONB** `attributes` column. This allows query flexibility without thousands of sparse columns.

| StatsBomb Field   | Our DB Column       | Type      |
| :---------------- | :------------------ | :-------- |
| `id`              | `id`                | UUID (PK) |
| `type.name`       | `type`              | String    |
| `timestamp`       | `minute` / `second` | Integer   |
| `location`        | `location_x/y`      | Float     |
| _Everything else_ | `attributes`        | **JSONB** |
