# Architecture Spec: Doppelgänger Engine (Beta)

**Date:** February 3, 2026
**Status:** APPROVED (v4 - Final)
**Feature:** Player Similarity Search (Vector Embeddings)

---

## 1. Overview

The **Doppelgänger Engine** is a "Moneyball"-style discovery tool designed to find players with statistically identical playstyles to a target player. By representing each player's season performance as a high-dimensional vector, we can mathematically calculate "playstyle similarity" using cosine distance.

**Critical Requirements:**

1.  **Context Aware**: Comparisons must respect position groups (FWD, MID, DEF, GK).
2.  **Temporal Specificity**: Players evolve. `Kane_2019` is a different entity from `Kane_2024`.
3.  **Explainability**: The system must explain _why_ a match was made, highlighting shared strengths and key differences.

---

## 2. Technical Architecture

### 2.1 The Pipeline

1.  **Data Extraction (ETL)**:
    - Query raw `Event` data from PostgreSQL.
    - Aggregate into `PlayerSeasonStats` (Intermediate DataFrame).
2.  **Feature Engineering**:
    - Normalize metrics (Per 90 mins).
    - Select relevant features (DNA of a player). _Note: Fixed feature set in Beta; v1 will introduce position-specific masking._
    - Scale features (Z-Score / StandardScaler).
3.  **Vectorization**:
    - Transform the dataset into a `Matrix (N_player_seasons x M_features)`.
    - **Entity Definition**: A vector represents a `(Player, Season, Position)` tuple.
4.  **Similarity Search**:
    - Use **k-Nearest Neighbors (k-NN)** with Cosine Similarity.
    - **Partitioning**: Training separate models per `position_group` (GK, DEF, MID, FWD).

### 2.2 Tech Stack Options

- **Libraries**: `pandas`, `scikit-learn` (StandardScaler, NearestNeighbors).
- **Storage**: In-memory `sklearn` models.
- **Resilience**: Models persist in memory; if the refresher job fails, the old model remains active.

---

## 3. Data Science Implementation

### 3.1 Feature Selection (The "DNA" Vector)

**Proposed Features (Per 90):**

1.  **Possession**: `passes_attempted`, `pass_completion_rate`, `progressive_passes`.
2.  **Attacking**: `shots_total`, `xg_total`, `dribbles_attempted`.
3.  **Defensive**: `pressures_applied`, `interceptions`, `tackles`.
4.  **Spatial**: `avg_action_x`, `avg_action_y`.

### 3.2 Normalization & Filters

- **MinInvolvement Filter**: Exclude player-seasons with < 300 minutes.
- **Scaling**: `StandardScaler`.

### 3.3 Interpretability Logic

To explain a match, we compare the scaled vectors of `Target` and `Match`.

- **Similarity Floor**: `distance < 0.30` (Equivalent to Cosine Sim > 0.70).
- **Shared Strengths**: Features where both players have Z-score > 0.8 (Top ~20%) OR Z-score < -0.8.
- **Key Difference**: The single feature with the largest absolute difference in Z-score between the two.
- **Distribution Check**: If no features meet the threshold, return "Balanced profile match".

---

## 4. API Specification

### Endpoint: `GET /analytics/doppelganger`

**Query Parameters:**

- `player_id` (int): ID of the target player.
- `season_id` (int): **Required**. The specific version of the player to match against.
- `position_group` (str, optional): Enforce matching only within a group ("FWD", "MID", "DEF"). Defaults to Target's position.
- `limit` (int): Number of matches to return. Default: 5, Max: 20.

**Response:**

```json
{
  "meta": {
    "model_version": "2026-02-03T04:00:00Z",
    "position_group": "FWD",
    "vector_count": 847
  },
  "target": { "name": "Harry Kane", "season": 2019, "position": "FWD" },
  "similar_players": [
    {
      "player_id": 123,
      "name": "Roberto Firmino",
      "season": 2019,
      "similarity_score": 0.98,
      "explanation": {
        "shared_strengths": ["Deep Drops (avg_action_x)", "High Pressing"],
        "key_difference": "Firmino has significantly higher tackles_per_90 (+1.2 SD)"
      }
    }
  ]
}
```

**Errors:**

- `404`: Player/Season not found.
- `422`: Insufficient data (Player < 300 mins).
- `200 Empty`: No matches found above 0.70 similarity threshold.

---

## 5. Implementation Roadmap

### Step 1: Core Logic

- Use `scikit-learn` to build the pipeline.
- Implement `PlayerSeasonVector` class to handle `(Player, Season)` identity.

### Step 2: Similarity Service

- **Refresher**: A background task (ARQ) re-trains the model daily.
- **Fail-safe**: Service tracks `last_updated` timestamp. If training yields < 50 vectors, discard and alert.

### Step 3: Explainability Module

- Function `explain_match` implementing the Z-score delta logic.

### Step 4: Pre-Launch Polish

- **Rate Limiting**: Enforce 60 req/min/user via `slowapi` or redis.
- **Dual-Position**: For Beta, use primary position (most minutes). Log edge cases where secondary > 30%.
- **Instrumentation**: Log query patterns (who users search for) to prioritize v1.
