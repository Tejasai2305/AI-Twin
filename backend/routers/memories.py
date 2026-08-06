from fastapi import APIRouter
from pydantic import BaseModel

from backend.services.memory_service import (
    get_memories,
    delete_memory,
    update_memory,
)

router = APIRouter()

class MemoryUpdate(BaseModel):
    memory: str
    importance: int

@router.get("/memories")
def get_all_memories():
    memories = get_memories()

    return [
        {
            "id": memory_id,
            "memory": memory,
            "importance": importance,
        }
        for memory_id, memory, importance in memories
    ]
@router.put("/memory/{memory_id}")
def update_memory_route(memory_id: int, update: MemoryUpdate):

    update_memory(
        memory_id,
        update.memory,
        update.importance,
    )

    return {
        "message": "Memory updated successfully."
    }

@router.delete("/memory/{memory_id}")
def remove_memory(memory_id: int):

    delete_memory(memory_id)

    return {
        "message": "Memory deleted successfully."
    }