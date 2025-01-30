import json
import os

def get_dataset():
    json_file_path = os.getenv("FEATURES_DATASET_PATH", "features_dataset.json")

    try:
        with open(json_file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error while reading features dataset from ({json_file_path}): {e}")
        return []


def initialize_features_dataset(r):
    dataset = get_dataset()

    for doc in dataset:
        key = f"week::{doc["week"]}::{doc["currency_code"]}"
        value = json.dumps(doc)
        r.execute_command("JSON.SET", key, "$", value)
