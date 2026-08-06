from backend.ai.memory_extractor import extract_memory
from backend.services.memory_manager import process_memory


def run_memory_stage(question):
    """
    Handles long-term memory extraction and updates.
    """

    memory = extract_memory(question.question)

    print("Memory Extractor Output:", memory)

    if memory.get("remember"):
        process_memory(memory["memory"])
    else:
        print("Nothing to remember.")