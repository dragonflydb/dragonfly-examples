from datetime import timedelta

from feast import Entity, FeatureView, Field, ValueType, FileSource
from feast.data_format import ParquetFormat
from feast.types import Float32, Int64, String

# Data Sources
users_file_source = FileSource(
    file_format=ParquetFormat(),
    path="data/users.parquet",
)

items_file_source = FileSource(
    file_format=ParquetFormat(),
    path="data/items.parquet",
)

interactions_file_source = FileSource(
    file_format=ParquetFormat(),
    path="data/interactions.parquet",
)

# Entities
user = Entity(name="user", value_type=ValueType.INT64, join_keys=["user_id"])
item = Entity(name="item", value_type=ValueType.INT64, join_keys=["item_id"])

# User Features
user_features = FeatureView(
    name="user_features",
    source=users_file_source,
    entities=[user],
    schema=[
        Field(name="age", dtype=Int64),
        Field(name="gender", dtype=String),
        Field(name="avg_rating", dtype=Float32),
        Field(name="preferred_category", dtype=String),
    ],
    ttl=timedelta(days=365),
)

# Item Features
item_features = FeatureView(
    name="item_features",
    source=items_file_source,
    entities=[item],
    schema=[
        Field(name="category", dtype=String),
        Field(name="price", dtype=Float32),
        Field(name="popularity_score", dtype=Float32),
        Field(name="avg_rating", dtype=Float32),
    ],
    ttl=timedelta(days=365),
)

# Interaction Features (User-Item Pairs)
interaction_features = FeatureView(
    name="interaction_features",
    source=interactions_file_source,
    entities=[user, item],
    schema=[
        Field(name="view_count", dtype=Int64),
        Field(name="last_rating", dtype=Float32),
        Field(name="time_since_last_interaction", dtype=Float32),
    ],
    ttl=timedelta(days=90),
)
