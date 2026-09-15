from pydantic import BaseModel, Field


class Conversation(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)


class ConversationResponse(BaseModel):
    id: int
    title: str
    status: str