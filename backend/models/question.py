from pydantic import BaseModel


class Question(BaseModel):
    conversation_id: int
    question: str