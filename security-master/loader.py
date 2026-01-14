from __future__ import annotations

import numpy as np
from redis import Redis as Dragonfly
from redis.commands.json.path import Path
from redis.commands.search.field import TextField, TagField, NumericField, VectorField
from redis.commands.search.index_definition import IndexDefinition, IndexType
from redis.exceptions import ResponseError
from sentence_transformers import SentenceTransformer

from dragonfly import connect_dragonfly
from generator import generate_security_master_record

_transformer_model = SentenceTransformer("all-MiniLM-L6-v2")
_transformer_model_dim = 384
_df = connect_dragonfly()


def ensure_index(df: Dragonfly, index_name: str = "idx"):
    try:
        schema = [
            TagField("$.ticker", as_name="ticker"),
            TagField("$.isin", as_name="isin"),
            TagField("$.security_description.exchange", as_name="exchange"),
            TagField("$.security_description.currency", as_name="currency"),
            TagField("$.security_description.sector", as_name="sector"),
            TextField("$.security_description.security_name", as_name="security_name"),
            NumericField("$.pricing_valuation.last_price", as_name="last_price"),
            NumericField("$.instrument_details.dividend_yield", as_name="dividend_yield"),
            VectorField(
                "$.security_general_description_embedding",
                as_name="security_general_description_embedding",
                algorithm="FLAT",
                attributes={
                    'TYPE': 'FLOAT32',
                    'DIM': _transformer_model_dim,
                    'DISTANCE_METRIC': 'COSINE'
                }
            ),
        ]
        definition = IndexDefinition(prefix=["sec:"], index_type=IndexType.JSON)
        df.ft(index_name).create_index(schema, definition=definition)
        print(f"Created index {index_name}")
    except ResponseError as e:
        if "Index already exists" in str(e):
            print(f"Index {index_name} already exists; skipping create.")
        else:
            raise


def main(n: int = 1000, step: int = 1000):
    ensure_index(_df, "idx:securities")

    pipeline = _df.pipeline(transaction=False)
    batch_count = 0

    for i in range(n):
        rec = generate_security_master_record(seed=i)
        embedding = _transformer_model.encode(rec.security_description.general_description)
        rec.security_general_description_embedding = embedding.astype(np.float32).tolist()

        key = f"sec:{rec.security_id}"
        payload = rec.model_dump(mode="json")
        pipeline.json().set(key, Path.root_path(), payload)
        batch_count += 1

        # Execute the pipeline when reaching the batch size.
        # After pipeline execution, reset the pipeline for the next batch.
        if batch_count >= step:
            pipeline.execute()
            print(f"Committed batch of {batch_count} records (up to #{i})")
            pipeline = _df.pipeline(transaction=False)
            batch_count = 0

    # Flush any remaining records
    if batch_count > 0:
        pipeline.execute()
        print(f"Committed final batch of {batch_count} records.")

    print(f"Loaded {n} security master records into Dragonfly.")


if __name__ == "__main__":
    main(1000)
