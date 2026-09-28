from backend.ai.memory_extractor import extract_memory
from backend.services.memory_conflict_detector import (
    save_memory_with_conflict_check,
)
from backend.services.conversation_service import get_conversation_owner
from backend.services.pipeline.pipeline_state import PipelineState


def run_memory_stage(state: PipelineState) -> PipelineState:
    """
    Handles long-term memory extraction and updates.
    """
    state.status = "🧠 Checking Memory..."
    memory = extract_memory(state.question.question)

    print("Memory Extractor Output:", memory)

    if memory.get("remember"):

        user_id = get_conversation_owner(state.question.conversation_id)

        result = save_memory_with_conflict_check(
            memory["memory"],
            importance=5,
            memory_type=memory.get("memory_type", "other"),
            source="conversation",
            confidence=memory.get("confidence", 0.7),
            evidence=memory.get("evidence"),
            user_id=user_id,
        )

        print("Memory:", result)

    else:
        print("Nothing to remember.")

    return state
