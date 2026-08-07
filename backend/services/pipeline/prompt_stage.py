from backend.services.pipeline.pipeline_state import PipelineState
from backend.services.prompt_builder import build_prompt


def run_prompt_stage(state: PipelineState) -> PipelineState:
    """
    Builds the final prompt for the LLM.
    """

    state.prompt = build_prompt(
        state.mode,
        state.history,
        state.notes,
        state.pdf,
        state.question.question,
    )

    return state