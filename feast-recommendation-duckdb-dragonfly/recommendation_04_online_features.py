from feast import FeatureStore


def fetch_online_features():
    store = FeatureStore(repo_path=".")

    online_features = store.get_online_features(
        features=[
            "user_features:age",
            "user_features:gender",
            "item_features:price",
            "interaction_features:view_count"
        ],
        entity_rows=[
            {"user_id": 1, "item_id": 101},
            {"user_id": 2, "item_id": 102}
        ]
    ).to_dict()

    print(online_features)


if __name__ == "__main__":
    fetch_online_features()
