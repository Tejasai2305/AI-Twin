from backend.services.pipeline.pipeline_state import PipelineState
from backend.services.pipeline.tool_stage import run_tool_stage
from backend.services.pipeline.memory_stage import run_memory_stage


def process_chat(question):
    """
    Main AI Pipeline
    """

    # Create pipeline state
    state = PipelineState(question=question)

    # -----------------------------
    # Stage 1: Tool
    # -----------------------------
    state = run_tool_stage(state)

    if state.handled:
        return {
            "handled": True,
            "response": state.tool_result,
        }

    # -----------------------------
    # Stage 2: Memory
    # -----------------------------
    state = run_memory_stage(state)

    return {
        "handled": False,
    }