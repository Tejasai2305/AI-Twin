from backend.services.pipeline.pipeline_state import PipelineState
from backend.services.retrieval_service import retrieve_context


def run_retrieval_stage(state: PipelineState) -> PipelineState:
    """
    Retrieves notes and PDF context.
    """
    state.status = "📄 Searching Knowledge..."
    notes_text, pdf_text, pdf_results = retrieve_context(
        state.mode,
        state.question.question,
    )

    state.notes = notes_text
    state.pdf = pdf_text
    state.pdf_results = pdf_results

    return state