from backend.services.pipeline.pipeline_state import PipelineState
from backend.services.router_service import classify_question
from backend.services.conversation_service import get_history


def run_history_stage(state: PipelineState) -> PipelineState:
    """
    Retrieves conversation history if needed.
    """

    state.mode = classify_question(
        state.question.question,
    )

    print(f"Mode: {state.mode}")

    if state.mode in ["conversation", "hybrid"]:
        state.history = get_history(
            state.question.conversation_id,
        )
    else:
        state.history = ""

    return state