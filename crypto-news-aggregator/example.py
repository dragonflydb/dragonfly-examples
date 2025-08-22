import json
import asyncio
import numpy as np
from redis import Redis
from datetime import datetime, timedelta
from news_fetcher import fetch_and_normalize_news_data
from weight_calculator import calculate_weight
from embedding_generator import generate_embedding
from features_dataset_initializer import initialize_features_dataset
from features_predictor import predict_growth


def get_key(article):
    return f"article::{article['id']}"


def get_article(r, key):
    return json.loads(r.execute_command("JSON.GET", key))


def set_article_field(r, key, field, value):
    return r.execute_command("JSON.SET", key, f"$.{field}", value)


async def update_article_weight(r, key):
    article = get_article(r, key)
    weight = calculate_weight(article)
    set_article_field(r, key, "weight", weight)


async def update_article_embedding(r, key):
    article = get_article(r, key)
    content = article.get("title", "")
    embedding = str(generate_embedding(content).tolist())
    set_article_field(r, key, "embedding", embedding)


def get_timestamp(days_ago=10):
    return int((datetime.now() - timedelta(days=days_ago)).timestamp())


def create_index(r):
    return r.execute_command(
        "FT.CREATE news_idx ON JSON PREFIX 1 article:: SCHEMA $.id AS id NUMERIC $.published_at AS published_at NUMERIC SORTABLE $.votes.negative AS votes_negative NUMERIC $.votes.positive AS votes_positive NUMERIC $.votes.important AS votes_important NUMERIC $.currencies[*].code AS currency_code TAG $.weight AS weight NUMERIC"
    )


def create_news_vector_index(r):
    return r.execute_command(
        "FT.CREATE news_vector_idx ON JSON PREFIX 1 article:: SCHEMA $.id AS id NUMERIC $.published_at AS published_at NUMERIC SORTABLE $.title AS title TEXT $.embedding AS embedding VECTOR FLAT 6 TYPE FLOAT32 DIM 384 DISTANCE_METRIC COSINE"
    )


def create_features_index(r):
    return r.execute_command(
        "FT.CREATE features_idx ON JSON PREFIX 1 week:: SCHEMA $.currency_code AS currency_code TAG $.features AS features VECTOR FLAT 6 TYPE FLOAT32 DIM 5 DISTANCE_METRIC COSINE $.label AS label NUMERIC"
    )


async def get_most_mentioned_cryptocurrencies(r, from_timestamp, top=10):
    return r.execute_command(
        "FT.AGGREGATE",
        "news_idx",
        f"@published_at:[{from_timestamp} +inf]",
        "GROUPBY",
        1,
        "@currency_code",
        "REDUCE",
        "COUNT",
        0,
        "AS",
        "mentions_count",
        "SORTBY",
        2,
        "@mentions_count",
        "DESC",
        "LIMIT",
        0,
        top,
    )


async def get_cryptocurrency_recent_mentions(r, currency, from_timestamp, limit=10):
    return r.execute_command(
        "FT.SEARCH",
        "news_idx",
        f"@currency_code:{{{currency}}} @published_at:[{from_timestamp} +inf]",
        "SORTBY",
        "published_at",
        "DESC",
        "LIMIT",
        0,
        limit,
    )


async def get_cryptocurrency_votes(r, currency, from_timestamp):
    return r.execute_command(
        "FT.AGGREGATE",
        "news_idx",
        f"@currency_code:{{{currency}}} @published_at:[{from_timestamp} +inf]",
        "GROUPBY",
        1,
        "@currency_code",
        "REDUCE",
        "SUM",
        1,
        "@votes_positive",
        "AS",
        "total_positive_votes",
        "REDUCE",
        "SUM",
        1,
        "@votes_negative",
        "AS",
        "total_negative_votes",
        "REDUCE",
        "SUM",
        1,
        "@votes_important",
        "AS",
        "total_important_votes",
    )


async def get_similar_articles(r, query_text, from_timestamp, top=10):
    query_embedding = generate_embedding(query_text).tobytes()
    return r.execute_command(
        "FT.SEARCH",
        "news_vector_idx",
        f"@published_at:[{from_timestamp} +inf] =>[KNN {top} @embedding $query AS score]",
        "PARAMS",
        2,
        "query",
        query_embedding,
        "SORTBY",
        "score",
        "ASC",
        "LIMIT",
        0,
        top,
        "RETURN",
        3,
        "title",
        "published_at",
        "score",
    )


def to_dict(result):
    if (len(result) < 2):
        return {}
    return {k.decode(): v.decode() for k, v in zip(result[1][::2], result[1][1::2])}


async def compute_features(r, currency, from_timestamp):
    recent_mensions = await get_cryptocurrency_recent_mentions(r, currency, from_timestamp, 1000)

    count_news = float(recent_mensions[0])

    votes = await get_cryptocurrency_votes(r, currency, from_timestamp)

    votes_dict = to_dict(votes)

    sum_positive = float(votes_dict.get("total_positive_votes", 0))
    sum_negative = float(votes_dict.get("total_negative_votes", 0))

    mean_positive = sum_positive / count_news if count_news > 0.0 else 0.0
    mean_negative = sum_negative / count_news if count_news > 0.0 else 0.0
    
    features = [count_news, sum_positive, sum_negative, mean_positive, mean_negative] #etc. 
    return np.array(features, dtype=np.float32)


async def cryptocurrency_will_grow(r, currency, from_timestamp):
    features = await compute_features(r, currency, from_timestamp)
    return await predict_growth(r, currency, features)


async def main():
    # Connect to DragonflyDB
    r = Redis(host="localhost", port=6379)

    r.execute_command("FLUSHALL")

    news_data = fetch_and_normalize_news_data()

    # Store the news data in DragonflyDB
    for article in news_data:
        key = get_key(article)
        value = json.dumps(article)
        r.execute_command("JSON.SET", key, "$", value)

    for article in news_data:
        key = get_key(article)
        await update_article_weight(r, key)

    for article in news_data:
        key = get_key(article)
        await update_article_embedding(r, key)

    create_index(r)
    create_news_vector_index(r)

    timestamp_ten_days_ago = 1700000000

    # Get the most mentioned cryptocurrencies
    print("Most mentioned cryptocurrencies:")
    print(await get_most_mentioned_cryptocurrencies(r, timestamp_ten_days_ago))
    print()

    # Get recent mentions of a cryptocurrency
    print("Recent mentions of BTC:")
    print(await get_cryptocurrency_recent_mentions(r, "BTC", timestamp_ten_days_ago, 2))
    print()

    # Get votes for a cryptocurrency
    print("Votes for BTC:")
    print(await get_cryptocurrency_votes(r, "BTC", timestamp_ten_days_ago))
    print()

    # Get similar articles
    print("Similar articles to 'Bitcoin crash':")
    print(await get_similar_articles(r, "Bitcoin crash", timestamp_ten_days_ago, 2))
    print()

    print("Similar articles to 'Ethereum rally':")
    print(await get_similar_articles(r, "Ethereum rally", timestamp_ten_days_ago, 2))
    print()

    print("Similar articles to 'Ripple lawsuit':")
    print(await get_similar_articles(r, "Ripple lawsuit", timestamp_ten_days_ago, 2))
    print()

    # Compute features for a cryptocurrency
    initialize_features_dataset(r)
    create_features_index(r)

    timestamp_seven_days_ago = 1730000000

    # Predict if a cryptocurrency will grow
    will_grow = await cryptocurrency_will_grow(r, "BTC", timestamp_seven_days_ago)
    print(f"Will BTC grow in next seven days? {"Yes" if will_grow else "No"}")


if __name__ == "__main__":
    asyncio.run(main())
