from sqlalchemy import Boolean, Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from database import Base


class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id = Column(Integer, primary_key=True)
    llm_name = Column(String, nullable=False)

    chat_histories = relationship("ChatHistory", back_populates="chat_session")


class ChatHistory(Base):
    __tablename__ = "chat_histories"

    id = Column(Integer, primary_key=True)
    chat_session_id = Column(Integer, ForeignKey("chat_sessions.id"), nullable=False)
    is_human_message = Column(Boolean, nullable=False)
    content = Column(String, nullable=False)
    metadata_completion_tokens = Column(Integer)
    metadata_prompt_tokens = Column(Integer)
    metadata_total_tokens = Column(Integer)
    metadata_system_fingerprint = Column(String)
    external_id = Column(String)

    chat_session = relationship("ChatSession", back_populates="chat_histories")
