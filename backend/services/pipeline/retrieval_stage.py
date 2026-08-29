from backend.services.pipeline.pipeline_state import PipelineState
from backend.services.retrieval_service import retrieve_context


def run_retrieval_stage(
    state: PipelineState
) -> PipelineState:

    state.status = "📄 Searching Knowledge..."

    conversation_id = (
        state.question.conversation_id
    )

    notes_text, pdf_text, pdf_results = (
        retrieve_context(
            state.mode,
            state.question.question,
            conversation_id
        )
    )

    state.notes = notes_text
    state.pdf = pdf_text
    state.pdf_results = pdf_results

    return state