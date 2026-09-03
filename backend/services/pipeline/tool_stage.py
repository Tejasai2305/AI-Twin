from backend.services.pipeline.pipeline_state import PipelineState
def run_tool_stage(state: PipelineState) -> PipelineState:
    """
    Executes tools only when the question is not an obvious
    knowledge/document request.
    """

    # Knowledge/document questions do not need Gemini tool routing.
    if state.mode == "knowledge":
        return state

    tool_result = process_request(
        state.question.question
    )

    if tool_result is not None:
        state.handled = True
        state.tool_result = tool_result

    return state