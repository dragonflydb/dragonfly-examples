from feast import FeatureService

from recommendation_02_repo import (
    user_features,
    item_features,
    interaction_features,
)

# FeatureService combines FeatureViews we defined earlier for recommendation use cases.
recommendation_feature_service = FeatureService(
    name="recommendation_service",
    features=[
        user_features,
        item_features,
        interaction_features,
    ],
)
