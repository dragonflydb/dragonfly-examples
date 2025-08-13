import pandas as pd

users = pd.DataFrame({
    "user_id": [1, 2, 3, 4, 5],
    "age": [25, 31, 45, 22, 38],
    "gender": ["M", "F", "F", "M", "M"],
    "avg_rating": [4.2, 3.8, 4.5, 3.2, 4.1],
    "preferred_category": ["electronics", "books", "clothing", "electronics", "home"],
    "event_timestamp": [pd.Timestamp("2025-08-28 00:00:00", tz="UTC") for _ in range(5)]
})

items = pd.DataFrame({
    "item_id": [101, 102, 103, 104, 105],
    "category": ["electronics", "books", "clothing", "electronics", "home"],
    "price": [299.99, 14.99, 49.99, 199.99, 89.99],
    "popularity_score": [0.85, 0.72, 0.91, 0.68, 0.77],
    "avg_rating": [4.3, 4.1, 4.7, 3.9, 4.2],
    "event_timestamp": [pd.Timestamp("2025-08-28 00:00:00", tz="UTC") for _ in range(5)]
})

interactions = pd.DataFrame({
    "user_id": [1, 1, 2, 3, 4, 5, 2, 3],
    "item_id": [101, 102, 103, 104, 105, 101, 102, 103],
    "view_count": [5, 2, 3, 1, 4, 2, 1, 3],
    "last_rating": [4.5, 3.5, 4.0, 3.0, 4.5, 4.0, 3.5, 4.5],
    "time_since_last_interaction": [2.5, 7.2, 1.0, 5.5, 0.5, 3.0, 8.0, 2.0],
    "event_timestamp": [pd.Timestamp("2025-08-28 00:00:00", tz="UTC") for _ in range(8)]
})

users.to_parquet("data/users.parquet", engine="pyarrow", index=False)
items.to_parquet("data/items.parquet", engine="pyarrow", index=False)
interactions.to_parquet("data/interactions.parquet", engine="pyarrow", index=False)
