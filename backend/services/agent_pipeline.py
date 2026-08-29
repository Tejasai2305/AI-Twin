from backend.services.pipeline.pipeline_state import PipelineState
from backend.services.pipeline.tool_stage import run_tool_stage
from backend.services.pipeline.memory_stage import run_memory_stage
from backend.services.pipeline.history_stage import run_history_stage
from backend.services.pipeline.retrieval_stage import run_retrieval_stage
from backend.services.pipeline.prompt_stage import run_prompt_stage
from backend.services.pipeline.llm_stage import run_llm_stage
from backend.services.pipeline.response_stage import build_response


def process_chat(question, generate_answer=True):

    state = PipelineState(question=question)

    # -----------------------------
    # Stage 1 - Tools
    # -----------------------------

    state = run_tool_stage(state)

    if state.handled:
        return {
            "handled": True,
            "response": state.tool_result,
        }

    # -----------------------------
    # Stage 2 - Memory
    # -----------------------------

    state = run_memory_stage(state)

    # -----------------------------
    # Stage 3 - Conversation History
    # -----------------------------

    state = run_history_stage(state)

    # -----------------------------
    # Stage 4 - Document Retrieval
    # -----------------------------

    state = run_retrieval_stage(state)

    # -----------------------------
    # Stage 5 - Prompt Construction
    # -----------------------------

    state = run_prompt_stage(state)

    # -----------------------------
    # Stage 6 - LLM
    # -----------------------------

    if generate_answer:
        state = run_llm_stage(state)

    return {
        "handled": False,
        "state": state,
        "response": build_response(state),
    }