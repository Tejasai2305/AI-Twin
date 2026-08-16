from backend.embeddings.memory_vector_store import search_memory
from backend.services.ai_memory_manager import decide_memory_action
from backend.services.memory_service import (
    add_memory,
    get_memory_by_text,
    update_memory,
)


def save_memory_with_conflict_check(new_memory: str, importance: int = 5):
    """
    AI-based memory manager.
    """

    # Find similar memories
    similar = search_memory(
        new_memory,
        top_k=5,
    )

    existing_memories = []

    for memory_text in similar:

        memory = get_memory_by_text(memory_text)

        if memory is None:
            continue

        memory_id, memory_text, memory_importance = memory

        existing_memories.append(
            {
                "id": memory_id,
                "memory": memory_text,
                "importance": memory_importance,
            }
        )

    # No similar memories
    if len(existing_memories) == 0:

        add_memory(
            new_memory,
            importance,
        )

        return "added"

    # Ask AI
    decision = decide_memory_action(
        existing_memories,
        new_memory,
    )

    action = decision.get("action")

    print("\nMemory Decision:")
    print(decision)

    # -------------------------
    # ADD
    # -------------------------

    if action == "add":

        add_memory(
            new_memory,
            importance,
        )

        return "added"

    # -------------------------
    # UPDATE
    # -------------------------

    if action == "update":

        update_memory(
            decision["memory_id"],
            new_memory,
            importance,
        )

        return "updated"

    # -------------------------
    # IGNORE
    # -------------------------

    if action == "ignore":

        return "ignored"

    # -------------------------
    # MERGE
    # -------------------------

    if action == "merge":

        update_memory(
            decision["memory_id"],
            decision["memory"],
            importance,
        )

        return "merged"

    # Fallback

    add_memory(
        new_memory,
        importance,
    )

    return "added"