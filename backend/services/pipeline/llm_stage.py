from backend.ai.gemini_service import ask_gemini
from backend.services.pipeline.pipeline_state import PipelineState


def run_llm_stage(state: PipelineState) -> PipelineState:
    """
    Sends the final prompt to Gemini.
    """

    state.answer = ask_gemini(
        state.prompt
    )

    return state