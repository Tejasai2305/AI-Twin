from backend.agent.controller import process_request


def run_tool_stage(question):
    """
    Executes tools (calculator, search, etc.).
    """

    tool_result = process_request(question.question)

    if tool_result is None:
        return {
            "handled": False,
            "tool_result": None,
        }

    return {
        "handled": True,
        "tool_result": tool_result,
    }