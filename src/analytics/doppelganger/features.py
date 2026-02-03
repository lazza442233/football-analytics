from typing import Dict, List

# Standard Feature Names (The "DNA")
FEATURES_BETA: List[str] = [
    # Possession
    "passes_attempted_per90",
    "pass_completion_rate",
    "progressive_passes_per90",
    "key_passes_per90",
    # Attacking
    "shots_total_per90",
    "xg_total_per90",
    "dribbles_attempted_per90",
    "progressive_carries_per90",
    "carry_distance_per90",
    # Defensive
    "pressures_applied_per90",
    "interceptions_per90",
    "tackles_per90",
    # Spatial
    "avg_action_x",
    "avg_action_y",
]

# Mapping from ETL output (raw/p90) to Feature DNA names
# keys: columns in stats_df from service/etl
# values: columns in df_features
COLUMN_MAPPING: Dict[str, str] = {
    "passes_attempted_p90": "passes_attempted_per90",
    "pass_completion_rate": "pass_completion_rate",
    "progressive_passes_p90": "progressive_passes_per90",
    "shot_assists_p90": "key_passes_per90",
    "shots_total_p90": "shots_total_per90",
    "xg_total_p90": "xg_total_per90",
    "dribbles_attempted_p90": "dribbles_attempted_per90",
    "progressive_carries_p90": "progressive_carries_per90",
    "carry_distance_p90": "carry_distance_per90",
    "pressures_applied_p90": "pressures_applied_per90",
    "interceptions_p90": "interceptions_per90",
    "tackles_p90": "tackles_per90",
    "avg_action_x": "avg_action_x",
    "avg_action_y": "avg_action_y",
}
