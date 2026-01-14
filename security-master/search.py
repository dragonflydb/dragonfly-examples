import numpy as np
from redis.commands.search.query import Query
from sentence_transformers import SentenceTransformer

from const import INDEX_NAME
from dragonfly import connect_dragonfly

_transformer_model = SentenceTransformer("all-MiniLM-L6-v2")
_transformer_model_dim = 384
_df = connect_dragonfly()


def vector_search(query: str):
    query_vec = _transformer_model.encode(query).astype(np.float32).tolist()
    query_expr = (Query("*=>[KNN 10 @security_general_description_embedding $query_vector AS vector_score]").
                  return_fields("security_id", "security_description", "vector_score").
                  sort_by("vector_score").
                  paging(0, 10))
    params = {"query_vector": np.array(query_vec).astype(dtype=np.float32).tobytes()}
    results = _df.ft(INDEX_NAME).search(query_expr, query_params=params).docs
    for _, doc in enumerate(results):
        print(doc.id)


if __name__ == "__main__":
    while True:
        user_input = input("Enter a query (or 'exit' to quit): ").strip()
        if user_input.lower() == "exit":
            break
        vector_search(user_input)
