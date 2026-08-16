from backend.services.pipeline.pipeline_state import PipelineState
from backend.services.prompt_builder import build_prompt


def run_prompt_stage(state: PipelineState) -> PipelineState:
    """
    Builds the final prompt for the LLM.
    """

    state.status = "Building prompt..."

    state.prompt = build_prompt(
        mode=state.mode,
        history=state.history,
        notes_text=state.notes,
        pdf_text=state.pdf,
        question=state.question.question,
    )

    return state