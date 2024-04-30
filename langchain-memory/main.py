from fastapi import FastAPI, Depends, HTTPException
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from langchain_openai import ChatOpenAI
from redis import Redis as Dragonfly, ConnectionPool
from sqlalchemy.orm import Session

import service
from database import SessionLocal
from schemas import ChatMessageCreate, ChatSessionCreate, ChatHistoryCreate

# Dependencies.
LARGE_LANGUAGE_MODEL_NAME = "gpt-3.5-turbo-1106"
chat_api_client = ChatOpenAI(model=LARGE_LANGUAGE_MODEL_NAME, temperature=0.2)
conn_pool = ConnectionPool(host='localhost', port=6379, db=0)
dragonfly_client = Dragonfly(connection_pool=conn_pool)


def get_chat():
    return chat_api_client


def get_db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_dragonfly():
    return dragonfly_client


# Create a new FastAPI server.
app = FastAPI()


@app.get("/")
def hello():
    return "Hello, LangChain! Hello, OpenAI!"


@app.post("/chat-without-memory")
async def chat_without_memory(
        chat_message_human: ChatMessageCreate,
        chat: ChatOpenAI = Depends(get_chat),
):
    message = HumanMessage(content=chat_message_human.content)
    chat_message = chat.invoke([message])
    return {"content": chat_message.content}


@app.post("/chat")
async def new_chat(
        chat_message_human: ChatMessageCreate,
        db: Session = Depends(get_db_session),
        df: Dragonfly = Depends(get_dragonfly),
        chat: ChatOpenAI = Depends(get_chat),
) -> service.ChatSessionResponse:
    # Invoke the OpenAI API to get the AI response.
    message = HumanMessage(content=chat_message_human.content)
    chat_message_ai = chat.invoke([message])

    # Create a new chat session with the first two chat history entries.
    chat_session = ChatSessionCreate(llm_name=LARGE_LANGUAGE_MODEL_NAME)
    new_chat_histories = __messages_to_histories(chat_message_human, chat_message_ai)
    srv = service.DataService(db, df)
    chat_session_response = srv.create_chat_session(chat_session, new_chat_histories)
    return chat_session_response


@app.patch("/chat/{chat_id}")
async def continue_chat(
        chat_id: int,
        chat_message_human: ChatMessageCreate,
        db: Session = Depends(get_db_session),
        df: Dragonfly = Depends(get_dragonfly),
        chat: ChatOpenAI = Depends(get_chat),
) -> service.ChatSessionResponse:
    # Check if the chat session exists and refresh the cache.
    srv = service.DataService(db, df)
    prev_chat_session_response = srv.read_chat_histories(chat_id)
    if prev_chat_session_response is None:
        raise HTTPException(status_code=404, detail="chat not found")

    # Construct messages from chat histories and then append the new human message.
    chat_histories = prev_chat_session_response.chat_histories
    messages = []
    for i in range(len(chat_histories)):
        if chat_histories[i].is_human_message:
            messages.append(HumanMessage(content=chat_histories[i].content))
        else:
            messages.append(AIMessage(content=chat_histories[i].content))
    messages.append(HumanMessage(content=chat_message_human.content))

    # Invoke the OpenAI API to get the AI response.
    chat_message_ai = chat.invoke(messages)

    # Add two chat history entries to an existing chat session.
    new_chat_histories = __messages_to_histories(chat_message_human, chat_message_ai)
    chat_session_response = srv.add_chat_histories(prev_chat_session_response, new_chat_histories)
    return chat_session_response


@app.get("/chat/{chat_id}")
async def read_chat_histories(
        chat_id: int,
        db: Session = Depends(get_db_session),
        df: Dragonfly = Depends(get_dragonfly),
) -> service.ChatSessionResponse:
    srv = service.DataService(db, df)
    chat_session_response = srv.read_chat_histories(chat_id)
    if chat_session_response is None:
        raise HTTPException(status_code=404, detail="chat not found")
    return chat_session_response


def __messages_to_histories(
        chat_message_human: ChatMessageCreate,
        chat_message_ai: BaseMessage,
) -> (ChatMessageCreate, ChatMessageCreate):
    chat_history_human = ChatHistoryCreate(
        is_human_message=True,
        content=chat_message_human.content,
    )
    chat_history_ai = ChatHistoryCreate(
        is_human_message=False,
        content=chat_message_ai.content,
        metadata_completion_tokens=chat_message_ai.response_metadata["token_usage"]["completion_tokens"],
        metadata_prompt_tokens=chat_message_ai.response_metadata["token_usage"]["prompt_tokens"],
        metadata_total_tokens=chat_message_ai.response_metadata["token_usage"]["total_tokens"],
        metadata_system_fingerprint=chat_message_ai.response_metadata["system_fingerprint"],
        external_id=chat_message_ai.id,
    )
    return chat_history_human, chat_history_ai
