from typing import Final

from fastapi import FastAPI, Depends, HTTPException
from redis import Redis as Dragonfly
from sqlalchemy.orm import Session
from web3 import Web3

import models
import utils
from deps import Deps

CACHE_NORMAL_EXPIRATION_SECONDS: Final[int] = 60
CACHE_EMPTY_EXPIRATION_SECONDS: Final[int] = 30

app = FastAPI()


@app.post("/transactions")
async def transaction(
        db: Session = Depends(Deps.get_db_session),
        df: Dragonfly = Depends(Deps.get_dragonfly),
        w3: Web3 = Depends(Deps.get_web3),
):
    return {"content": "OK"}


@app.get("/transactions/{id}")
async def get_transaction(
        id: int,
        db: Session = Depends(Deps.get_db_session),
        df: Dragonfly = Depends(Deps.get_dragonfly),
) -> utils.TransactionResponse:
    cache_key = utils.txn_cache_key(id)

    # Try to read the transaction from Dragonfly first.
    cached_txn = await df.hgetall(cache_key)
    if cached_txn is not None:
        if cached_txn:
            return utils.txn_dict_to_response(cached_txn)
        else:
            raise HTTPException(status_code=404, detail="Transaction not found")

    # Cache miss, read from the database.
    txn = db.query(models.UserAccountTransaction) \
        .filter(models.UserAccountTransaction.id == id) \
        .first()

    # If the transaction is not found, cache an empty value and return a 404.
    # Caching an empty value is important to prevent cache penetrations.
    if txn is None:
        await df.hset(cache_key, mapping={})
        await df.expire(cache_key, CACHE_EMPTY_EXPIRATION_SECONDS)
        raise HTTPException(status_code=404, detail="Transaction not found")

    # Cache the transaction in Dragonfly and return the response.
    await df.hset(cache_key, mapping=utils.txn_to_dict(txn))
    await df.expire(cache_key, CACHE_NORMAL_EXPIRATION_SECONDS)
    return utils.txn_to_response(txn)
