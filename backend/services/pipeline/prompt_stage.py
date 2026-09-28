from backend.services.pipeline.pipeline_state import PipelineState
from backend.services.prompt_builder import build_prompt
from backend.services.conversation_service import get_conversation_owner


def run_prompt_stage(state: PipelineState) -> PipelineState:
    """
    Builds the final prompt for the LLM.
    """

    state.status = "Building prompt..."

    user_id = get_conversation_owner(state.question.conversation_id)

    state.prompt = build_prompt(
        mode=state.mode,
        history=state.history,
        notes_text=state.notes,
        pdf_text=state.pdf,
        question=state.question.question,
        user_id=user_id,
    )

    return state
