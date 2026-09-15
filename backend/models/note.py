from pydantic import BaseModel, Field


class Note(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)
    content: str = Field(..., min_length=1, max_length=20000)


class NoteResponse(BaseModel):
    title: str
    content: str
    status: str