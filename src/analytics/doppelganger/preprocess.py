import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler

from src.analytics.doppelganger.features import COLUMN_MAPPING, FEATURES_BETA


def build_feature_frame(stats_df: pd.DataFrame) -> pd.DataFrame:
    """
    Transforms the raw aggregated stats into the 'DNA' feature matrix.
    1. Selects relevant columns (renaming per schema).
    2. Imputes missing values.
    3. Clamps rates.
    """
    if stats_df.empty:
        return pd.DataFrame(columns=FEATURES_BETA)

    # 1. Rename to Standard Feature Names
    df = stats_df.rename(columns=COLUMN_MAPPING)

    # Ensure all features exist
    for feature in FEATURES_BETA:
        if feature not in df.columns:
            df[feature] = np.nan

    # Subselect
    df = df[FEATURES_BETA].copy()

    # 2. Imputation Strategy
    # Zero Fill: "Absence" metrics (No action = 0 per 90)
    # Median Fill: Rates & Spatial (Avoid skewing distribution with 0s)

    zeros_cols = [c for c in FEATURES_BETA if "rate" not in c and "avg" not in c]
    median_cols = [c for c in FEATURES_BETA if "rate" in c or "avg" in c]

    # Fill 'Absence' metrics with 0.0
    df[zeros_cols] = df[zeros_cols].fillna(0.0)

    # Fill Rates/Spatial with Median
    # Note: We use the median of the current batch (season dataset).
    # If the entire column is NaN (no data for anyone), fallback to 0 or center.
    medians = df[median_cols].median()
    df[median_cols] = df[median_cols].fillna(medians)

    # Final cleanup for edge case where median is NaN
    df = df.fillna(0.0)

    # 3. Clamp Rates
    if "pass_completion_rate" in df.columns:
        df["pass_completion_rate"] = df["pass_completion_rate"].clip(0.0, 1.0)

    return df


def fit_scaler(df_features: pd.DataFrame) -> StandardScaler:
    """
    Fits a StandardScaler to the feature matrix.
    Returns the fitted scaler object.
    Typically applied per position group subset.
    """
    scaler = StandardScaler()
    # Ensure we only fit on the beta feature set
    if df_features.empty:
        return scaler

    scaler.fit(df_features)
    return scaler
