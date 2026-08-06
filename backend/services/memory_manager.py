from backend.ai.memory_conflict_detector import detect_memory_conflict
from backend.embeddings.memory_vector_store import search_memory
from backend.services.memory_service import (
    add_memory,
    update_memory_text,
)


def process_memory(new_memory):
    print("\n========== MEMORY MANAGER ==========")
    print("Candidate:", new_memory)

    similar = search_memory(new_memory, top_k=3)

    print("Similar Memories:", similar)

    decision = detect_memory_conflict(
        new_memory,
        similar,
    )

    print("Decision:", decision)

    action = decision.get("action")

    if action == "insert":

        add_memory(new_memory)

        print("Inserted.")

    elif action == "update":

        update_memory_text(
            decision["existing_memory"],
            new_memory,
        )

        print("Updated.")

    elif action == "ignore":

        print("Ignored duplicate.")

    else:

        print("Unknown action.")