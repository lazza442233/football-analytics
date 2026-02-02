import pandas as pd

from src.analytics.doppelganger.config import (
    EVENT_TYPE_MAPPINGS,
    MIN_MINUTES,
    NORMALIZE_PER_90_COLS,
    POSITION_MAPPINGS,
)


def estimate_minutes_played(events_df: pd.DataFrame) -> pd.Series:
    """
    Estimates minutes played for each player in each season.
    Approximation: Sum(max_event_minute - min_event_minute) per match.
    Refined logic:
    - Caps at 90 + stoppage (approx 100)
    - Adds buffer for subs (e.g. if events span 5 mins, assume slightly
      more active time)
    """
    if events_df.empty:
        return pd.Series(dtype=float)

    def calculate_window(minutes: pd.Series) -> float:
        if minutes.empty:
            return 0.0

        # Explicit type casting for mypy strictness
        mn = float(minutes.min())
        mx = float(minutes.max())

        # Heuristic: If first action is < 5 and last > 85, likely full match
        if mn < 5 and mx > 85:
            return 90.0  # Cap standard match

        diff = mx - mn
        # Add buffer for "active play" outside events
        estimated = diff + 5.0
        return float(min(estimated, 90.0))

    # Group by season, match, player to get the active window
    match_windows = events_df.groupby(["season_id", "match_id", "player_id"])[
        "minute"
    ].agg(calculate_window)

    season_minutes = match_windows.groupby(["season_id", "player_id"]).sum()
    season_minutes.name = "minutes_played"

    return season_minutes


def assign_position_group(player_metadata: pd.DataFrame) -> pd.Series:
    """
    Maps raw specific positions to groups (FWD, MID, DEF, GK).
    Expects player_metadata to have 'id' and 'position'.
    Returns Series indexed by player_id.
    """
    if "position" not in player_metadata.columns:
        return pd.Series(dtype="object")

    return (
        player_metadata.set_index("id")["position"]
        .map(POSITION_MAPPINGS)
        .fillna("UNKNOWN")
    )


def calculate_advanced_metrics(events_df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculates specific metrics required for the Doppelgänger DNA.
    Extracts data from the 'attributes' JSON column.
    """
    # 1. Base Type Counts
    base_stats = pd.crosstab(
        index=[events_df["season_id"], events_df["player_id"]],
        columns=events_df["type"],
    )

    # Map raw types to feature names
    mappings = EVENT_TYPE_MAPPINGS

    # Rename and ensure columns exist
    df_metrics = base_stats.rename(columns=mappings)
    for col in mappings.values():
        if col not in df_metrics.columns:
            df_metrics[col] = 0

    # 2. Complex Metrics (xG, Completion Rate) using attributes

    # xG (Expected Goals)
    shot_mask = events_df["type"] == "Shot"
    if shot_mask.any():
        shots = events_df[shot_mask].copy()
        # Assume flattened 'xg' key for simplicity
        shots["xg"] = shots["attributes"].apply(
            lambda x: x.get("xg", 0.0) if isinstance(x, dict) else 0.0
        )
        xg_stats = (
            shots.groupby(["season_id", "player_id"])["xg"].sum().rename("xg_total")
        )
        df_metrics = df_metrics.join(xg_stats, how="left").fillna({"xg_total": 0})
    else:
        df_metrics["xg_total"] = 0.0

    # Pass Completion
    pass_mask = events_df["type"] == "Pass"
    if pass_mask.any():
        passes = events_df[pass_mask].copy()
        # Assume if 'outcome' is missing, it's complete
        passes["is_complete"] = passes["attributes"].apply(
            lambda x: 1 if (isinstance(x, dict) and x.get("outcome") is None) else 0
        )
        completed_stats = (
            passes.groupby(["season_id", "player_id"])["is_complete"]
            .sum()
            .rename("passes_completed")
        )
        df_metrics = df_metrics.join(completed_stats, how="left").fillna(
            {"passes_completed": 0}
        )

        # Calculate Rate
        df_metrics["pass_completion_rate"] = df_metrics[
            "passes_completed"
        ] / df_metrics["passes_attempted"].replace(0, 1)

        # Progressive Passes (Approx: moved ball > 10m towards goal or into box)
        # We need start (location_x, location_y) and end.
        pass_end = passes["attributes"].apply(
            lambda x: x.get("end_location", []) if isinstance(x, dict) else []
        )

        # We need to vectorized this check if possible, or apply per row
        # Simple heuristic: end_x is significantly > start_x (assuming x=120 is goal)
        # StatsBomb x: 0-120. y: 0-80.
        def is_progressive(row, end_loc):
            if not end_loc or len(end_loc) < 2:
                return 0
            start_x = row["location_x"] or 0
            end_x = end_loc[0]
            dist_forward = end_x - start_x

            # Criteria: 10 yards forward (approx 9m? SB coords are yards)
            # OR into penalty box (x > 102, y between 18 and 62)
            is_into_box = (
                (end_x >= 102) and (18 <= end_loc[1] <= 62) and (start_x < 102)
            )
            return 1 if (dist_forward >= 10) or is_into_box else 0

        # We can't vectorise easily with mismatching lists, so use apply with the series
        # Note: pandas apply with axis=1 is slow, but acceptable for Beta volume
        # Optimization: use lists
        passes["end_loc"] = pass_end
        passes["is_progressive"] = passes.apply(
            lambda r: is_progressive(r, r["end_loc"]), axis=1
        )

        prog_stats = (
            passes.groupby(["season_id", "player_id"])["is_progressive"]
            .sum()
            .rename("progressive_passes")
        )
        df_metrics = df_metrics.join(prog_stats, how="left").fillna(
            {"progressive_passes": 0}
        )

    else:
        df_metrics["passes_completed"] = 0
        df_metrics["pass_completion_rate"] = 0.0
        df_metrics["progressive_passes"] = 0

    # Spatial: Average Action Location
    # Using specific columns now available in repo
    if "location_x" in events_df.columns and "location_y" in events_df.columns:
        spatial = events_df.groupby(["season_id", "player_id"])[
            ["location_x", "location_y"]
        ].mean()
        spatial = spatial.rename(
            columns={"location_x": "avg_action_x", "location_y": "avg_action_y"}
        )
        df_metrics = df_metrics.join(spatial, how="left")
    else:
        # Fallback if columns missing (should not happen with new repo)
        df_metrics["avg_action_x"] = 50.0
        df_metrics["avg_action_y"] = 40.0

    return df_metrics


def aggregate_player_season_stats(events_df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregates raw events into a player-season stats table.
    """
    if events_df.empty:
        return pd.DataFrame()

    # 1. Calculate Metrics
    stats = calculate_advanced_metrics(events_df)

    # 2. Estimate Minutes
    minutes = estimate_minutes_played(events_df)

    # Join
    stats = stats.join(minutes, how="inner")

    # 3. Filter
    stats = stats[stats["minutes_played"] >= MIN_MINUTES].copy()

    if stats.empty:
        return pd.DataFrame()

    # 4. Normalize Per 90 (Only count-based metrics)
    normalize_cols = NORMALIZE_PER_90_COLS
    for col in normalize_cols:
        if col in stats.columns:
            stats[f"{col}_p90"] = (stats[col] / stats["minutes_played"]) * 90

    return stats
