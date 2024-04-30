CREATE TABLE chat_sessions
(
    id       INTEGER PRIMARY KEY,
    llm_name TEXT NOT NULL
);

CREATE TABLE chat_histories
(
    id                          INTEGER PRIMARY KEY,
    chat_session_id             INTEGER NOT NULL,
    is_human_message            INTEGER NOT NULL,
    content                     TEXT    NOT NULL,
    metadata_completion_tokens  INTEGER,
    metadata_prompt_tokens      INTEGER,
    metadata_total_tokens       INTEGER,
    metadata_system_fingerprint INTEGER,
    external_id                 TEXT,
    FOREIGN KEY (chat_session_id) REFERENCES chat_sessions (id)
);
