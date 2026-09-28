from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from backend.embeddings.memory_vector_store import search_memory
from backend.auth.dependencies import get_optional_user
from backend.services.memory_service import (
    get_memories,
    add_memory,
    delete_memory,
    update_memory,
    get_memories_detailed,
    get_memory_detail,
    get_memory_history,
    deactivate_memory,
    reactivate_memory,
    get_memory_chain,
    get_contradictions,
    VALID_MEMORY_TYPES,
)

router = APIRouter()


class MemoryCreate(BaseModel):
    memory: str = Field(..., min_length=1, max_length=2000)
    importance: int = Field(default=5, ge=1, le=10)
    memory_type: str = Field(default="other")
    source: str = Field(default="conversation")
    source_reference: str | None = None
    confidence: float = Field(default=0.7, ge=0.0, le=1.0)


class MemoryUpdate(BaseModel):
    memory: str = Field(..., min_length=1, max_length=2000)
    importance: int = Field(..., ge=1, le=10)
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    evidence: str | None = None


def _uid(current_user):
    """None when unauthenticated (no-auth/single-user mode) - matches
    every service function's default, which preserves exact original
    (unfiltered) behavior when auth isn't in use at all."""
    return current_user["id"] if current_user else None


def _assert_owned(memory_id, current_user):
    """
    Ownership check for by-ID operations. When auth is in use, a
    memory owned by user_id IS NOT NULL and belonging to someone else
    (or unowned/legacy) must not be readable or modifiable by this
    account. When auth is not in use, behaves exactly as before
    (404 only if the id doesn't exist at all).
    """
    detail = get_memory_detail(memory_id)
    if detail is None:
        raise HTTPException(status_code=404, detail="Memory not found.")

    if current_user is not None and detail["user_id"] != current_user["id"]:
        # Same response as "doesn't exist" - never reveal that a
        # memory exists but belongs to someone else.
        raise HTTPException(status_code=404, detail="Memory not found.")

    return detail


# -----------------------------
# Get All Memories
# -----------------------------

@router.get("/memories")
def get_all_memories(current_user=Depends(get_optional_user)):

    try:
        memories = get_memories(user_id=_uid(current_user))

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
def semantic_memory_search(query: str, current_user=Depends(get_optional_user)):

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
        return search_memory(query, user_id=_uid(current_user))

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
def create_memory(data: MemoryCreate, current_user=Depends(get_optional_user)):

    memory = data.memory.strip()

    if not memory:
        raise HTTPException(
            status_code=400,
            detail="Memory cannot be empty.",
        )

    memory_type = data.memory_type if data.memory_type in VALID_MEMORY_TYPES else "other"

    try:
        add_memory(
            memory,
            data.importance,
            memory_type=memory_type,
            source=data.source,
            source_reference=data.source_reference,
            confidence=data.confidence,
            user_id=_uid(current_user),
        )

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
def remove_memory(memory_id: int, current_user=Depends(get_optional_user)):

    try:
        _assert_owned(memory_id, current_user)

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
    current_user=Depends(get_optional_user),
):

    memory = update.memory.strip()

    if not memory:
        raise HTTPException(
            status_code=400,
            detail="Memory cannot be empty.",
        )

    try:
        _assert_owned(memory_id, current_user)

        update_memory(
            memory_id,
            memory,
            update.importance,
            confidence=update.confidence,
            evidence=update.evidence,
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


# -----------------------------
# Memory Center: detailed listing (confidence, source, evidence,
# type, active/inactive) — additive, does not replace /memories
# -----------------------------

@router.get("/memories/detailed")
def get_all_memories_detailed(
    memory_type: str | None = None,
    include_inactive: bool = False,
    current_user=Depends(get_optional_user),
):
    try:
        if memory_type and memory_type not in VALID_MEMORY_TYPES:
            raise HTTPException(status_code=400, detail="Unknown memory_type.")

        return get_memories_detailed(
            memory_type=memory_type,
            include_inactive=include_inactive,
            user_id=_uid(current_user),
        )

    except HTTPException:
        raise
    except Exception as e:
        print("Detailed memory retrieval error:", e)
        raise HTTPException(status_code=500, detail="Unable to retrieve memories.")


@router.get("/memory/{memory_id}/detail")
def get_memory_detail_route(memory_id: int, current_user=Depends(get_optional_user)):
    return _assert_owned(memory_id, current_user)


@router.get("/memory/{memory_id}/history")
def get_memory_history_route(memory_id: int, current_user=Depends(get_optional_user)):
    _assert_owned(memory_id, current_user)
    return get_memory_history(memory_id)


@router.get("/memory/{memory_id}/timeline")
def get_memory_timeline_route(memory_id: int, current_user=Depends(get_optional_user)):
    """
    Full temporal chain for this memory's subject (Feature 4):
    every value it has ever held, oldest to newest, each with the
    window (valid_from -> valid_until) during which it was the
    current fact. The most recent entry has valid_until = None,
    meaning it is still current.
    """
    _assert_owned(memory_id, current_user)
    return get_memory_chain(memory_id)


@router.post("/memory/{memory_id}/deactivate")
def deactivate_memory_route(memory_id: int, current_user=Depends(get_optional_user)):
    _assert_owned(memory_id, current_user)
    deactivate_memory(memory_id)
    return {"message": "Memory deactivated."}


@router.post("/memory/{memory_id}/reactivate")
def reactivate_memory_route(memory_id: int, current_user=Depends(get_optional_user)):
    _assert_owned(memory_id, current_user)
    reactivate_memory(memory_id)
    return {"message": "Memory reactivated."}


@router.get("/memory/types")
def list_memory_types():
    return sorted(VALID_MEMORY_TYPES)


# -----------------------------
# Contradiction feed: every time the AI memory manager resolved a
# contradiction (old fact replaced by a new one), it's tagged in
# memory_history as 'contradiction_resolved'. This surfaces that
# audit trail so the user can see what changed and why, rather than
# facts silently overwriting each other.
# -----------------------------

@router.get("/memory/contradictions")
def list_contradictions(limit: int = 50, current_user=Depends(get_optional_user)):
    try:
        return get_contradictions(limit=limit, user_id=_uid(current_user))
    except Exception as e:
        print("Contradiction listing error:", e)
        raise HTTPException(status_code=500, detail="Unable to retrieve contradictions.")
