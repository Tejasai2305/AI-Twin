from pydantic import BaseModel


class Conversation(BaseModel):
    title: str


class ConversationResponse(BaseModel):
    id: int
    title: str
    status: str