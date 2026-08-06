from pydantic import BaseModel


class Message(BaseModel):
    conversation_id: int
    role: str
    content: str