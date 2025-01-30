import json


def parse_search_result(result):
    docs = result[2::2]
    return [json.loads(doc[1].decode()) for doc in docs]


# Simple KNN-based predictor
async def predict_growth(r, currency, new_features, k=5):
    query_vector = new_features.tobytes()
    
    search_result = r.execute_command(
        "FT.SEARCH", "features_idx", "*",  
        f"@currency_code:{{{currency}}} =>[KNN {k} @features $query_vec AS score]",
        "PARAMS", "2", "query_vec", query_vector
    )

    results = parse_search_result(search_result)

    knn_labels = [doc["label"] for doc in results]
    return 1 if sum(knn_labels) > len(knn_labels) / 2 else 0