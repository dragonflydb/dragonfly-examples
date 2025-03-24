def calculate_weight(article):
    votes = article.get("votes", {})
    weight = (
        votes.get("positive", 0)
        + votes.get("important", 0) * 2
        - votes.get("negative", 0)
    )
    return weight
