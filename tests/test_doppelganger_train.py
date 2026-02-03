import pandas as pd
from sklearn.neighbors import NearestNeighbors
from sklearn.preprocessing import StandardScaler

from src.analytics.doppelganger import features, model, preprocess, registry, train


def test_player_season_vector_creation():
    vec = model.PlayerSeasonVector(
        player_id=1,
        season_id=2023,
        position_group="FWD",
        name="Lennon",
        minutes_played=900.0,
    )
    assert vec.name == "Lennon"
    assert vec.minutes_played == 900.0


def test_train_model_for_group():
    # 1. Create Mock Stats DF
    # Needs to match what comes out of ETL -> has _p90 columns
    # Create 3 'players' with similar stats
    data = []
    for i in range(10):
        row = {
            "player_id": 100 + i,
            "season_id": 2023,
            "name": f"Player {i}",
            "minutes_played": 1000.0,
            "position_group": "FWD",
            # Add feature columns
            "passes_attempted_p90": 30.0 + i,  # varying
            "pass_completion_rate": 0.8,
            "avg_action_x": 50.0,
            "avg_action_y": 50.0,
        }
        data.append(row)

    df_group = pd.DataFrame(data).set_index(["season_id", "player_id"])

    # Train
    bundle = train.train_model_for_group(df_group, "FWD")

    # Assertions
    assert isinstance(bundle, model.PositionModelBundle)
    assert bundle.position_group == "FWD"
    assert bundle.vector_count == 10

    # Check artifacts
    assert isinstance(bundle.scaler, StandardScaler)
    assert isinstance(bundle.knn, NearestNeighbors)

    # Check Entities
    assert len(bundle.entities) == 10
    assert bundle.entities[0].player_id == 100
    assert bundle.entities[9].player_id == 109


def test_knn_sanity_check():
    """
    Ensure the KNN model actually finds neighbors.
    """
    # Create 2 clusters of players
    # Cluster A: High Pass Volume (50 p90)
    # Cluster B: Low Pass Volume (10 p90)

    data = []
    # 5 Players in Cluster A
    for i in range(5):
        data.append(
            {
                "player_id": i,
                "season_id": 2023,
                "name": f"A-{i}",
                "minutes_played": 500,
                "passes_attempted_p90": 50.0 + (i * 0.1),  # vary slightly
            }
        )
    # 5 Players in Cluster B
    for i in range(5, 10):
        data.append(
            {
                "player_id": i,
                "season_id": 2023,
                "name": f"B-{i}",
                "minutes_played": 500,
                "passes_attempted_p90": 10.0 + (i * 0.1),
            }
        )

    df = pd.DataFrame(data).set_index(["season_id", "player_id"])

    bundle = train.train_model_for_group(df, "TEST")

    # Query for Player 0 (Cluster A)
    # We need to manually transform the vector for query simulation
    p0_features = bundle.entities[0]  # Should match index 0
    assert p0_features.player_id == 0

    # Get raw features for player 0
    # In real flow we pass the vector. Here we hack it from the scaling matrix for test.
    # The KNN is fitted on Scaled X.

    # Let's verify 'kneighbors' returns indices 0,1,2,3,4 as closest
    X_scaled = bundle.scaler.transform(
        preprocess.build_feature_frame(df)[features.FEATURES_BETA]
    )

    # Query nearest 3 neighbors for vector 0
    # Must preserve 2D shape for sklearn
    query_vector = X_scaled[0].reshape(1, -1)

    distances, indices = bundle.knn.kneighbors(query_vector, n_neighbors=3)

    # Indices should be from Cluster A (0-4)
    found_indices = indices[0]
    for idx in found_indices:
        assert idx < 5, f"Found neighbor {idx} from Cluster B which should be far away"


def test_registry():
    reg = registry.ModelRegistry()

    # Create fake bundle
    bundle = model.PositionModelBundle(
        position_group="FWD",
        vector_count=0,
        entities=[],
        scaler=StandardScaler(),
        knn=NearestNeighbors(),
        feature_names=[],
    )

    reg.register("FWD", bundle)

    assert reg.get("FWD") == bundle
    assert reg.get("DEF") is None

    assert reg.status["FWD"] == 0
