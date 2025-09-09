import pandas as pd
from feast import FeatureStore


def fetch_historical_features():
    store = FeatureStore(repo_path=".")

    # Build an entity dataframe as input.
    entity_df = pd.DataFrame({
        "user_id": [1, 2],
        "item_id": [101, 102],
        "event_timestamp": [pd.Timestamp("2025-08-28 00:00:00", tz="UTC") for _ in range(2)]
    })

    # Specify which features to retrieve.
    features = [
        "user_features:age",
        "user_features:gender",
        "item_features:price",
        "interaction_features:view_count"
    ]

    historical_df = store.get_historical_features(
        entity_df=entity_df,
        features=features
    ).to_df()

    print(historical_df)


if __name__ == "__main__":
    fetch_historical_features()
