from typing import Dict, List

import numpy as np


def explain_match(
    target_z: np.ndarray, match_z: np.ndarray, feature_names: List[str]
) -> Dict[str, object]:
    """
    Generates a human-readable explanation for why two players are considered similar
    based on their standardized (Z-score) feature vectors.

    Args:
        target_z: Standardized feature vector for the target player.
        match_z: Standardized feature vector for the matched player.
        feature_names: List of feature names corresponding to the vector indices.

    Returns:
        A dictionary containing:
        - 'shared_strengths': List of features where both players have significant
          positive deviation (> 0.8) or negative deviation (< -0.8).
        - 'key_difference': A string describing the feature with the largest divergence.
    """
    if len(target_z) != len(match_z) or len(target_z) != len(feature_names):
        raise ValueError("Input vectors and feature names must have the same length.")

    shared_strengths = []

    # Threshold for what constitutes a "significant" characteristic
    # Z-score > 0.8 means top ~21% of distribution
    # Z-score < -0.8 means bottom ~21% of distribution
    SIGNIFICANCE_THRESHOLD = 0.8

    # 1. Identify Shared Strengths
    for i, feature in enumerate(feature_names):
        t_val = target_z[i]
        m_val = match_z[i]

        # Check for high positive correlation (both significantly above average)
        if t_val > SIGNIFICANCE_THRESHOLD and m_val > SIGNIFICANCE_THRESHOLD:
            shared_strengths.append(f"High {feature}")

        # Check for high negative correlation (both significantly below average)
        elif t_val < -SIGNIFICANCE_THRESHOLD and m_val < -SIGNIFICANCE_THRESHOLD:
            shared_strengths.append(f"Low {feature}")

    # Fallback if no specific extremes are shared
    if not shared_strengths:
        shared_strengths.append("Balanced profile match")

    # 2. Identify Key Difference
    # Calculate absolute difference vector
    diffs = np.abs(target_z - match_z)

    # Find index of maximum difference
    max_diff_idx = np.argmax(diffs)
    max_diff_val = diffs[max_diff_idx]
    max_diff_feature = feature_names[max_diff_idx]

    # Signed difference to explain directionality relative to target
    # e.g. if target=1.0 and match=0.5, delta is -0.5 (Match is lower)
    # e.g. if target=0.5 and match=1.0, delta is +0.5 (Match is higher)
    # Let's frame it as "Match has {delta} {feature}" relative to target

    # Spec says: "{feature} differs by {delta:+.2f} SD"
    # Usually we want to know how the match differs from the target.
    # If delta is large, it's the defining distinction.

    difference_desc = f"{max_diff_feature} differs by {max_diff_val:.2f} SD"

    # Edge case: Identical vectors
    if max_diff_val < 0.001:
        difference_desc = "Profiles are statistically identical"

    return {"shared_strengths": shared_strengths, "key_difference": difference_desc}
