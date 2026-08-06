from backend.ai.gemini_service import ask_gemini
from backend.agent.tool_prompt import TOOL_PROMPT
from backend.agent.json_utils import extract_json


def detect_tool(user_message: str):
    """
    Ask Gemini whether a tool should be used.
    """

    prompt = f"""
{TOOL_PROMPT}

User:
{user_message}
"""

    response = ask_gemini(prompt)

    print("\n========== TOOL ROUTER ==========")
    print("Raw Gemini Response:")
    print(response)

    tool = extract_json(response)

    if tool is None:
        print("Failed to extract valid JSON.")
        return None

    # -----------------------------
    # Validation
    # -----------------------------
    if "tool" not in tool:
        print("Missing 'tool' key.")
        return None

    if tool["tool"] == "none":
        print("No tool selected.")
        return None

    if "arguments" not in tool:
        print("Missing 'arguments' key.")
        return None

    print("Validated Tool:")
    print(tool)

    return tool