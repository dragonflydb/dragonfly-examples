import os
import json

def fetch_and_normalize_news_data():
    json_file_path = os.getenv("NEWS_DATASET_PATH", "news_dataset.json")

    try:
        with open(json_file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error while reading news dataset from ({json_file_path}): {e}")
        return []