from typing import Optional

from pydantic import BaseModel


# For creating new sessions, excluding IDs and relations.
class ChatSessionCreate(BaseModel):
    llm_name: str


class ChatMessageCreate(BaseModel):
    content: str


# For creating new history entries, excluding IDs and relations.
class ChatHistoryCreate(ChatMessageCreate):
    is_human_message: bool
    metadata_completion_tokens: Optional[int] = None
    metadata_prompt_tokens: Optional[int] = None
    metadata_total_tokens: Optional[int] = None
    metadata_system_fingerprint: Optional[str] = None
    external_id: Optional[str] = None
