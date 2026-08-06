from backend.services.pipeline.memory_stage import run_memory_stage


def process_chat(question):
    """
    Main AI pipeline.
    """

    # Stage 1
    run_memory_stage(question)

    return {
        "handled": False
    }