import logging

import pandas as pd
from sklearn.neighbors import NearestNeighbors

from src.analytics.doppelganger import features, preprocess
from src.analytics.doppelganger.config import MAX_LIMIT
from src.analytics.doppelganger.model import PlayerSeasonVector, PositionModelBundle

logger = logging.getLogger(__name__)


def train_model_for_group(
    df_group: pd.DataFrame, position_group: str
) -> PositionModelBundle:
    """
    Trains the KNN model and Scaler for a specific position group.

    Args:
        df_group: DataFrame containing player stats + metadata for one position.
                  Index is expected to be (season_id, player_id) or just range index
                  provided columns specific to that are present.

    Returns:
        PositionModelBundle containing the artifacts.
    """
    # 1. Prepare Metadata Entities (Preserving Order)
    # Ensure we don't drop rows during feature engineering implicitly
    # It is assumed df_group is already filtered for eligibility (min minutes etc)

    entities = []

    # We iterate over the DataFrame to build the metadata list.
    # This list's order MUST match the X matrix rows.
    # We use itertuples for speed, but need to be careful with index if it's MultiIndex.

    # Reset index to ensure we can access player_id/season_id easily
    df_meta = df_group.reset_index(drop=False)

    # Ensure required metadata columns exist
    # 'name' might be missing if not joined yet, but typically passed in.
    # If missing, provide fallback
    if "name" not in df_meta.columns:
        df_meta["name"] = "Unknown"

    for _idx, row in df_meta.iterrows():
        entity = PlayerSeasonVector(
            player_id=int(row["player_id"]),
            season_id=int(row["season_id"]),
            position_group=position_group,
            name=str(row["name"]),
            minutes_played=float(row.get("minutes_played", 0.0)),
        )
        entities.append(entity)

    # 2. Build Feature Matrix X
    df_features = preprocess.build_feature_frame(df_group)

    # 3. Fit Scaler
    scaler = preprocess.fit_scaler(df_features)

    # 4. Transform Matrix
    X_scaled = scaler.transform(df_features[features.FEATURES_BETA])

    # 5. Fit KNN
    # n_neighbors: We need at least MAX_LIMIT + 1 (for self)
    # If we have fewer samples than n_neighbors, use count
    n_samples = len(entities)
    k = min(n_samples, MAX_LIMIT + 1)

    knn = NearestNeighbors(n_neighbors=k, metric="cosine")
    knn.fit(X_scaled)

    bundle = PositionModelBundle(
        position_group=position_group,
        vector_count=n_samples,
        entities=entities,
        scaler=scaler,
        knn=knn,
        feature_names=features.FEATURES_BETA,
    )

    logger.info(f"Trained KNN for {position_group} with {n_samples} vectors.")
    return bundle
