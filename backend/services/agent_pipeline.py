from backend.services.pipeline.pipeline_state import PipelineState
from backend.services.pipeline.tool_stage import run_tool_stage
from backend.services.pipeline.memory_stage import run_memory_stage
from backend.services.pipeline.history_stage import run_history_stage
from backend.services.pipeline.retrieval_stage import run_retrieval_stage
from backend.services.pipeline.prompt_stage import run_prompt_stage
from backend.services.pipeline.llm_stage import run_llm_stage
from backend.services.pipeline.response_stage import build_response


def process_chat(question):

    state = PipelineState(question=question)

    # Stage 1
    state = run_tool_stage(state)

    if state.handled:
        return {
            "handled": True,
            "response": state.tool_result,
        }

    # Stage 2
    state = run_memory_stage(state)

    # Stage 3
    state = run_history_stage(state)

    # Stage 4
    state = run_retrieval_stage(state)

    # Stage 5
    state = run_prompt_stage(state)

    # Stage 6
    state = run_llm_stage(state)

    return {
        "handled": False,
        "state": state,
        "response": build_response(state),
    }   