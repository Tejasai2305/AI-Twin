from backend.services.pipeline.pipeline_state import PipelineState
from backend.services.router_service import classify_question
from backend.services.conversation_service import get_history


def run_history_stage(state: PipelineState) -> PipelineState:
    """
    Retrieves conversation history if needed.
    """

    state.status = "Loading Conversation..."

    state.mode = classify_question(
        state.question.question,
    )

    conversation_id = state.question.conversation_id

    print("\n========== HISTORY DEBUG ==========")
    print("Conversation ID:", conversation_id)
    print("Question:", state.question.question)
    print("Mode:", state.mode)

    if state.mode in ["conversation", "hybrid"]:
        state.history = get_history(conversation_id)
    else:
        state.history = ""

    print("History:")
    print(repr(state.history))
    print("===================================\n")

    return state