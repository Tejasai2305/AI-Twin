from backend.services.pipeline.tool_stage import run_tool_stage
from backend.services.pipeline.memory_stage import run_memory_stage


def process_chat(question):
    """
    Main AI pipeline.
    """

    # Stage 1: Check for tools first
    tool = run_tool_stage(question)

    if tool["handled"]:
        return {
            "handled": True,
            "response": tool["tool_result"],
        }

    # Stage 2: Only process memory for normal chat
    run_memory_stage(question)

    return {
        "handled": False,
    }