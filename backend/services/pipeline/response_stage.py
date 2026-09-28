from backend.services.pipeline.pipeline_state import PipelineState


def build_response(state: PipelineState):
    """
    Build the final API response.
    """

    return {
        "question": state.question.question,
        "answer": state.answer,
        "mode": state.mode,
        "sources": [
            {
                "file": result["filename"],
                "chunk": result["chunk_id"],
            }
            for result in state.pdf_results
        ],
    }