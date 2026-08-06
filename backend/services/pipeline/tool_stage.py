from backend.agent.controller import process_request
from backend.services.pipeline.pipeline_state import PipelineState


def run_tool_stage(state: PipelineState) -> PipelineState:
    """
    Executes tools (calculator, search, etc.).
    """

    tool_result = process_request(state.question.question)

    if tool_result is not None:
        state.handled = True
        state.tool_result = tool_result

    return state