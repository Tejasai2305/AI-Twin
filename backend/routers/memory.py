from fastapi import APIRouter
from backend.embeddings.memory_vector_store import search_memory
from backend.services.memory_service import (
    get_memories,
    add_memory,
    delete_memory,
    update_memory,
)
from pydantic import BaseModel
router = APIRouter()

class MemoryUpdate(BaseModel):
    memory: str
    importance: int
# -----------------------------
# Get All Memories
# -----------------------------
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
# -----------------------------
# Semantic Memory Search
# -----------------------------
@router.get("/memory/search")
def semantic_memory_search(query: str):

    results = search_memory(query)

    return results

# -----------------------------
# Add Memory
# -----------------------------
@router.post("/memory")
def create_memory(data: dict):

    memory = data.get("memory")

    importance = data.get("importance", 5)

    add_memory(memory, importance)

    return {
        "message": "Memory added successfully."
    }


# -----------------------------
# Delete Memory
# -----------------------------
@router.delete("/memory/{memory_id}")
def remove_memory(memory_id: int):

    delete_memory(memory_id)

    return {
        "message": "Memory deleted successfully."
    }


# -----------------------------
# Update Importance
# -----------------------------
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