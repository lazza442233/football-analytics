import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler

from src.analytics.doppelganger import features, preprocess


def test_build_feature_frame_structure():
    # Input with some mapped columns
    data = {
        "passes_attempted_p90": [50.0],
        "xg_total_p90": [0.5],
        # Missing columns should be created as 0 or NaN then imputed
    }
    df_in = pd.DataFrame(data)

    df_out = preprocess.build_feature_frame(df_in)

    # Check columns match Feature Beta
    assert list(df_out.columns) == features.FEATURES_BETA

    # Check renaming worked
    assert df_out["passes_attempted_per90"].iloc[0] == 50.0
    assert df_out["xg_total_per90"].iloc[0] == 0.5


def test_build_feature_frame_imputation():
    # Case: Missing data
    # row 0: valid data
    # row 1: NaNs
    data = {
        "passes_attempted_p90": [50.0, np.nan],
        "pass_completion_rate": [0.8, np.nan],  # Rate -> Median
        "avg_action_x": [60.0, np.nan],  # Spatial -> Median
        "tackles_p90": [2.0, np.nan],  # Count -> 0 dummy
    }
    df_in = pd.DataFrame(data)

    df_out = preprocess.build_feature_frame(df_in)

    # Row 1 (Index 1) Check

    # Count metrics -> 0.0
    assert df_out["passes_attempted_per90"].iloc[1] == 0.0
    assert df_out["tackles_per90"].iloc[1] == 0.0

    # Rates/Spatial -> Median
    # Batch median for completion: 0.8 (only 1 valid value) -> 0.8
    assert df_out["pass_completion_rate"].iloc[1] == 0.8
    # Batch median for x: 60.0
    assert df_out["avg_action_x"].iloc[1] == 60.0


def test_build_feature_frame_clamping():
    data = {"pass_completion_rate": [1.5, -0.1, 0.5]}
    df_in = pd.DataFrame(data)
    df_out = preprocess.build_feature_frame(df_in)

    # 1.5 -> 1.0
    assert df_out["pass_completion_rate"].iloc[0] == 1.0
    # -0.1 -> 0.0
    assert df_out["pass_completion_rate"].iloc[1] == 0.0
    # 0.5 -> 0.5
    assert df_out["pass_completion_rate"].iloc[2] == 0.5


def test_fit_scaler():
    # Setup simple frame
    data = []
    for i in range(10):
        row = {f: float(i) for f in features.FEATURES_BETA}
        data.append(row)

    df = pd.DataFrame(data)

    scaler = preprocess.fit_scaler(df)

    assert isinstance(scaler, StandardScaler)
    assert scaler.mean_ is not None
    assert len(scaler.mean_) == len(features.FEATURES_BETA)

    # Test transform logic works
    transformed = scaler.transform(df[features.FEATURES_BETA])
    assert transformed.shape == (10, len(features.FEATURES_BETA))
