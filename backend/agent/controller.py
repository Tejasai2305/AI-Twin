from backend.agent.tool_router import detect_tool
from backend.agent.tool_executor import execute_tool


def process_request(user_message: str):
    """
    Main entry point for the AI Agent.
    """

    tool = detect_tool(user_message)

    if tool is None:
        return None

    result = execute_tool(
        tool["tool"],
        tool["arguments"],
    )

    return {
        "tool_used": tool["tool"],
        "result": result,
    }