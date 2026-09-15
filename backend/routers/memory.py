from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backend.embeddings.memory_vector_store import search_memory
from backend.services.memory_service import (
    get_memories,
    add_memory,
    delete_memory,
    update_memory,
)

router = APIRouter()


class MemoryCreate(BaseModel):
    memory: str = Field(..., min_length=1, max_length=2000)
    importance: int = Field(default=5, ge=1, le=10)


class MemoryUpdate(BaseModel):
    memory: str = Field(..., min_length=1, max_length=2000)
    importance: int = Field(..., ge=1, le=10)


# -----------------------------
# Get All Memories
# -----------------------------

@router.get("/memories")
def get_all_memories():

    try:
        memories = get_memories()

        return [
            {
                "id": memory_id,
                "memory": memory,
                "importance": importance,
            }
            for memory_id, memory, importance in memories
        ]

    except Exception as e:
        print("Memory retrieval error:", e)
        raise HTTPException(
            status_code=500,
            detail="Unable to retrieve memories.",
        )


# -----------------------------
# Semantic Memory Search
# -----------------------------

@router.get("/memory/search")
def semantic_memory_search(query: str):

    query = query.strip()

    if not query:
        raise HTTPException(
            status_code=400,
            detail="Search query cannot be empty.",
        )

    if len(query) > 500:
        raise HTTPException(
            status_code=400,
            detail="Search query is too long.",
        )

    try:
        return search_memory(query)

    except Exception as e:
        print("Memory search error:", e)
        raise HTTPException(
            status_code=500,
            detail="Unable to search memories.",
        )


# -----------------------------
# Add Memory
# -----------------------------

@router.post("/memory")
def create_memory(data: MemoryCreate):

    memory = data.memory.strip()

    if not memory:
        raise HTTPException(
            status_code=400,
            detail="Memory cannot be empty.",
        )

    try:
        add_memory(memory, data.importance)

        return {
            "message": "Memory added successfully."
        }

    except Exception as e:
        print("Memory creation error:", e)
        raise HTTPException(
            status_code=500,
            detail="Unable to add memory.",
        )


# -----------------------------
# Delete Memory
# -----------------------------

@router.delete("/memory/{memory_id}")
def remove_memory(memory_id: int):

    try:
        memories = get_memories()

        if not any(item[0] == memory_id for item in memories):
            raise HTTPException(
                status_code=404,
                detail="Memory not found.",
            )

        delete_memory(memory_id)

        return {
            "message": "Memory deleted successfully."
        }

    except HTTPException:
        raise

    except Exception as e:
        print("Memory deletion error:", e)
        raise HTTPException(
            status_code=500,
            detail="Unable to delete memory.",
        )


# -----------------------------
# Update Memory
# -----------------------------

@router.put("/memory/{memory_id}")
def update_memory_route(
    memory_id: int,
    update: MemoryUpdate,
):

    memory = update.memory.strip()

    if not memory:
        raise HTTPException(
            status_code=400,
            detail="Memory cannot be empty.",
        )

    try:
        memories = get_memories()

        if not any(item[0] == memory_id for item in memories):
            raise HTTPException(
                status_code=404,
                detail="Memory not found.",
            )

        update_memory(
            memory_id,
            memory,
            update.importance,
        )

        return {
            "message": "Memory updated successfully."
        }

    except HTTPException:
        raise

    except Exception as e:
        print("Memory update error:", e)
        raise HTTPException(
            status_code=500,
            detail="Unable to update memory.",
        )