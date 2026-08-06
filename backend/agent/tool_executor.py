from backend.tools.calculator import execute as calculator_execute
from backend.tools.search import execute as search_execute

TOOLS = {
    "calculator": calculator_execute,
    "search": search_execute,
}


def execute_tool(tool_name: str, arguments: dict):
    """
    Execute any registered tool.
    """

    tool = TOOLS.get(tool_name)

    if tool is None:
        return {
            "success": False,
            "error": f"Unknown tool: {tool_name}"
        }

    return tool(**arguments)