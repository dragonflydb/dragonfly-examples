CREATE TABLE user_accounts
(
    id                       INTEGER PRIMARY KEY,
    available_balance_in_wei INTEGER NOT NULL,
    current_balance_in_wei   INTEGER NOT NULL
);

CREATE TABLE user_account_transactions
(
    id                                INTEGER PRIMARY KEY,
    user_account_id                   INTEGER REFERENCES user_accounts (id) NOT NULL,
    transaction_hash                  TEXT                                  NOT NULL,
    from_public_address               TEXT                                  NOT NULL,
    to_public_address                 TEXT                                  NOT NULL,
    transaction_amount_in_wei         INTEGER                               NOT NULL,
    transaction_fee_total_in_wei      INTEGER                               NOT NULL,
    transaction_fee_blockchain_in_wei INTEGER                               NOT NULL,
    status                            INTEGER                               NOT NULL DEFAULT 0 CHECK (status IN (0, 1, 2))
);

CREATE INDEX idx_user_account_id ON user_account_transactions (user_account_id);
