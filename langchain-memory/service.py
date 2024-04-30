from dataclasses import dataclass
from typing import List, Union

from fastapi import HTTPException
from redis import Redis as Dragonfly
from sqlalchemy.orm import Session

import models
import schemas


@dataclass
class ChatHistoryResponse:
    id: int
    content: str
    is_human_message: bool


@dataclass
class ChatSessionResponse:
    chat_session_id: int
    chat_histories: List[ChatHistoryResponse]


class DataService:
    def __init__(self, db: Session, df: Dragonfly):
        self.db = db
        self.df = df

    # Create a new chat session with the first two chat history entries.
    # The first chat history entry is a prompt (human message), and the second is a response (AI message).
    def create_chat_session(
            self,
            new_chat_session: schemas.ChatSessionCreate,
            new_chat_histories: (schemas.ChatHistoryCreate, schemas.ChatHistoryCreate)
    ) -> ChatSessionResponse:
        # Create a new chat session.
        chat_session = models.ChatSession(llm_name=new_chat_session.llm_name)
        self.db.add(chat_session)
        self.db.flush()

        # Add the first two chat history entries for the chat session.
        chat_history_human = self.__chat_history_schema_to_model(chat_session.id, new_chat_histories[0])
        chat_history_ai = self.__chat_history_schema_to_model(chat_session.id, new_chat_histories[1])
        self.db.add_all([chat_history_human, chat_history_ai])
        self.db.commit()
        self.db.refresh(chat_session)

        # Since this is a new chat session, and the user will likely want to continue this chat session.
        # We will cache the chat history entries in Dragonfly.
        ru = _DataCacheService(self.df)
        chat_histories = [chat_history_human, chat_history_ai]
        chat_history_responses = [ChatHistoryResponse(v.id, v.content, v.is_human_message) for v in chat_histories]
        ru.add_chat_histories(chat_session.id, chat_history_responses)
        return ChatSessionResponse(chat_session.id, chat_history_responses)

    # Add two chat history entries to an existing chat session.
    # The first chat history entry is a prompt (human message), and the second is a response (AI message).
    # Handler much call 'self.read_chat_histories' before calling this method.
    def add_chat_histories(
            self,
            prev_chat_session_response: ChatSessionResponse,
            new_chat_histories: (schemas.ChatHistoryCreate, schemas.ChatHistoryCreate),
    ) -> ChatSessionResponse:
        # Add the new chat history entries.
        chat_session_id = prev_chat_session_response.chat_session_id
        chat_history_human = self.__chat_history_schema_to_model(chat_session_id, new_chat_histories[0])
        chat_history_ai = self.__chat_history_schema_to_model(chat_session_id, new_chat_histories[1])
        self.db.add_all([chat_history_human, chat_history_ai])
        self.db.commit()

        # Cache the chat history entries in Dragonfly.
        ru = _DataCacheService(self.df)
        chat_histories = [chat_history_human, chat_history_ai]
        chat_history_responses = [ChatHistoryResponse(v.id, v.content, v.is_human_message) for v in chat_histories]
        ru.add_chat_histories(chat_session_id, chat_history_responses)
        prev_chat_session_response.chat_histories.extend(chat_history_responses)
        return prev_chat_session_response

    # Read all chat history entries for a chat session.
    def read_chat_histories(self, chat_session_id: int) -> Union[ChatSessionResponse, None]:
        # Check if the chat history entries are cached in Dragonfly.
        ru = _DataCacheService(self.df)
        chat_history_responses = ru.read_chat_histories(chat_session_id)
        if chat_history_responses is not None and len(chat_history_responses) > 0:
            return ChatSessionResponse(chat_session_id, chat_history_responses)
        # If the chat history entries are not cached in Dragonfly, read from the database.
        # Then cache them in Dragonfly.
        chat_histories = self.db.query(models.ChatHistory) \
            .filter(models.ChatHistory.chat_session_id == chat_session_id) \
            .order_by(models.ChatHistory.id) \
            .all()
        if chat_histories is None or len(chat_histories) == 0:
            return None
        chat_history_responses = [ChatHistoryResponse(v.id, v.content, v.is_human_message) for v in chat_histories]
        ru.add_chat_histories(chat_session_id, chat_history_responses)
        return ChatSessionResponse(chat_session_id, chat_history_responses)

    @staticmethod
    def __chat_history_schema_to_model(
            chat_session_id: int,
            chat_history: schemas.ChatHistoryCreate,
    ):
        return models.ChatHistory(
            chat_session_id=chat_session_id,
            is_human_message=chat_history.is_human_message,
            content=chat_history.content,
            metadata_completion_tokens=chat_history.metadata_completion_tokens,
            metadata_prompt_tokens=chat_history.metadata_prompt_tokens,
            metadata_total_tokens=chat_history.metadata_total_tokens,
            metadata_system_fingerprint=chat_history.metadata_system_fingerprint,
            external_id=chat_history.external_id,
        )


class _DataCacheService:
    HUMAN_MESSAGE_PREFIX = "H:"
    AI_MESSAGE_PREFIX = "A:"

    def __init__(self, df: Dragonfly):
        self.df = df

    @staticmethod
    def key_chat_histories(chat_session_id: int) -> str:
        return f"chat_histories_by_session_id:{chat_session_id}"

    @staticmethod
    def chat_history_tuple_to_response(chat_history: (str, float)) -> ChatHistoryResponse:
        # Note that the sorted-set value is the content, and the score is the ID.
        prefixed_content = chat_history[0].decode('utf-8', errors='replace')
        if len(prefixed_content) < 2:
            raise HTTPException(status_code=500, detail="failed to parse chat history")
        prefix, content = prefixed_content[:2], prefixed_content[2:]
        return ChatHistoryResponse(
            id=int(chat_history[1]),
            content=content,
            is_human_message=(prefix == _DataCacheService.HUMAN_MESSAGE_PREFIX),
        )

    def add_chat_histories(self, chat_session_id: int, chat_histories: List[ChatHistoryResponse]) -> ():
        key = self.key_chat_histories(chat_session_id)
        mapping = {}
        for history in chat_histories:
            prefix = self.HUMAN_MESSAGE_PREFIX if history.is_human_message else self.AI_MESSAGE_PREFIX
            mapping[f"{prefix}{history.content}"] = history.id
        self.df.zadd(
            name=key,
            mapping=mapping,
        )
        self.df.expire(name=key, time=60 * 60)

    def read_chat_histories(self, chat_session_id: int) -> List[ChatHistoryResponse]:
        key = self.key_chat_histories(chat_session_id)
        histories = self.df.zrange(name=key, start=0, end=-1, withscores=True)
        return [self.chat_history_tuple_to_response(history) for history in histories]
