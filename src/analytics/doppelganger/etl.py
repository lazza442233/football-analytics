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
    Approximation: Sum(max_event_minute - min_event_minute) per match with a buffer.
    """
    if events_df.empty:
        return pd.Series(dtype=float)

    def calculate_window(minutes: pd.Series) -> float:
        if minutes.empty:
            return 0.0

        mn = float(minutes.min())
        mx = float(minutes.max())

        # Heuristic: If first action is < 5 and last > 85, likely full match
        if mn < 5 and mx > 85:
            return 90.0

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
    """
    # 1. Base Type Counts
    base_stats = pd.crosstab(
        index=[events_df["season_id"], events_df["player_id"]],
        columns=events_df["type"],
    )

    mappings = EVENT_TYPE_MAPPINGS

    df_metrics = base_stats.rename(columns=mappings)
    for col in mappings.values():
        if col not in df_metrics.columns:
            df_metrics[col] = 0

    # 2. Complex Metrics (xG, Completion Rate)

    # xG (Expected Goals)
    shot_mask = events_df["type"] == "Shot"
    if shot_mask.any():
        shots = events_df[shot_mask].copy()
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
        # If 'outcome' is missing, it's complete
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
        pass_end = passes["attributes"].apply(
            lambda x: x.get("end_location", []) if isinstance(x, dict) else []
        )

        def is_progressive(row, end_loc):
            if not end_loc or len(end_loc) < 2:
                return 0
            start_x = row["location_x"] or 0
            end_x = end_loc[0]
            dist_forward = end_x - start_x

            # Criteria: 10 yards forward
            # OR into penalty box (x > 102, y between 18 and 62)
            is_into_box = (
                (end_x >= 102) and (18 <= end_loc[1] <= 62) and (start_x < 102)
            )
            return 1 if (dist_forward >= 10) or is_into_box else 0

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
    if "location_x" in events_df.columns and "location_y" in events_df.columns:
        spatial = events_df.groupby(["season_id", "player_id"])[
            ["location_x", "location_y"]
        ].mean()
        spatial = spatial.rename(
            columns={"location_x": "avg_action_x", "location_y": "avg_action_y"}
        )
        df_metrics = df_metrics.join(spatial, how="left")
    else:
        df_metrics["avg_action_x"] = 50.0
        df_metrics["avg_action_y"] = 40.0

    return df_metrics


def aggregate_player_season_stats(events_df: pd.DataFrame) -> pd.DataFrame:
    if events_df.empty:
        return pd.DataFrame()

    stats = calculate_advanced_metrics(events_df)
    minutes = estimate_minutes_played(events_df)

    # Normalize stats columns by 90 minutes
    # Join minutes

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
