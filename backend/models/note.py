from pydantic import BaseModel


class Note(BaseModel):
    title: str
    content: str


class NoteResponse(BaseModel):
    title: str
    content: str
    status: str