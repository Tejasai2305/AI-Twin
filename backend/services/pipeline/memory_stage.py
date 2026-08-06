from backend.ai.memory_extractor import extract_memory
from backend.services.memory_manager import process_memory
from backend.services.pipeline.pipeline_state import PipelineState


def run_memory_stage(state: PipelineState) -> PipelineState:
    """
    Handles long-term memory extraction and updates.
    """

    memory = extract_memory(state.question.question)

    print("Memory Extractor Output:", memory)

    if memory.get("remember"):
        process_memory(memory["memory"])
    else:
        print("Nothing to remember.")

    return state