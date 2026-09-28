from backend.embeddings.memory_vector_store import search_memory
from backend.services.ai_memory_manager import decide_memory_action
from backend.services.memory_service import (
    add_memory,
    get_memory_by_text,
    update_memory,
    supersede_memory,
)


def save_memory_with_conflict_check(
    new_memory: str,
    importance: int = 5,
    memory_type: str = "other",
    source: str = "conversation",
    source_reference: str = None,
    confidence: float = 0.7,
    evidence: str = None,
    user_id: int = None,
):
    """
    AI-based memory manager.

    Returns a dict describing what happened, including whether a
    contradiction was detected, so callers (and the Memory Center UI)
    can surface it rather than silently overwriting a prior fact.

    user_id=None (default) preserves exact original behavior when
    auth isn't in use - candidates are drawn only from unowned/legacy
    memories, matching search_memory()'s own default. When a user_id
    is given, every step (search, lookup, save) stays scoped to that
    user only, so two accounts can never merge/contradict/see each
    other's facts.
    """

    # Find similar memories
    similar = search_memory(
        new_memory,
        top_k=5,
        user_id=user_id,
    )

    existing_memories = []

    for memory_text in similar:

        memory = get_memory_by_text(memory_text, user_id=user_id)

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
            memory_type=memory_type,
            source=source,
            source_reference=source_reference,
            confidence=confidence,
            evidence=evidence,
            user_id=user_id,
        )

        return {"action": "added"}

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
            memory_type=memory_type,
            source=source,
            source_reference=source_reference,
            confidence=confidence,
            evidence=evidence,
            user_id=user_id,
        )

        return {"action": "added"}

    # -------------------------
    # UPDATE (this is a contradiction: the new fact replaces an
    # old one for the same subject. We supersede rather than mutate
    # in place, so the old value + when it stopped being true is
    # preserved for temporal queries / the Memory Center timeline.
    # supersede_memory() inherits the owner from the old row itself,
    # so it stays correct without needing user_id passed explicitly -
    # and existing_memories was already scoped to this user above, so
    # decision["memory_id"] can only be one of this user's own facts.)
    # -------------------------

    if action == "update":

        old_entry = next(
            (m for m in existing_memories if m["id"] == decision.get("memory_id")),
            None,
        )

        new_id = supersede_memory(
            decision["memory_id"],
            new_memory,
            importance,
            memory_type=memory_type,
            source=source,
            source_reference=source_reference,
            confidence=confidence,
            evidence=evidence,
        )

        return {
            "action": "updated",
            "memory_id": new_id,
            "previous_memory_id": decision["memory_id"],
            "previous_value": old_entry["memory"] if old_entry else None,
            "new_value": new_memory,
        }

    # -------------------------
    # IGNORE
    # -------------------------

    if action == "ignore":

        return {"action": "ignored"}

    # -------------------------
    # MERGE
    # -------------------------

    if action == "merge":

        update_memory(
            decision["memory_id"],
            decision["memory"],
            importance,
            confidence=confidence,
            evidence=evidence,
            action="merged",
        )

        return {"action": "merged", "memory_id": decision["memory_id"]}

    # Fallback

    add_memory(
        new_memory,
        importance,
        memory_type=memory_type,
        source=source,
        source_reference=source_reference,
        confidence=confidence,
        evidence=evidence,
        user_id=user_id,
    )

    return {"action": "added"}
