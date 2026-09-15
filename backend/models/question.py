from pydantic import BaseModel, Field


class Question(BaseModel):
    conversation_id: int = Field(..., ge=1)
    question: str = Field(..., min_length=1, max_length=10000)