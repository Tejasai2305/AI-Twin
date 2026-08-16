from backend.ai.gemini_service import ask_gemini
from backend.agent.tool_prompt import TOOL_PROMPT
from backend.agent.json_utils import extract_json

import re
def is_math_expression(text: str) -> bool:
    """
    Detect simple arithmetic expressions.
    """

    text = text.strip()

    return bool(
        re.fullmatch(
            r"[0-9\.\+\-\*/\(\)\%\s]+",
            text
        )
    )


def is_search_query(text: str) -> bool:
    """
    Detect requests that clearly need web search.
    """

    text = text.lower()

    keywords = [
        "latest",
        "news",
        "today",
        "current",
        "recent",
        "search",
        "lookup",
        "find on internet",
        "web",
    ]

    return any(keyword in text for keyword in keywords)
def detect_tool(user_message: str):
    """
    Hybrid Tool Router.
    """

    # -----------------------------
    # Fast Rule-Based Routing
    # -----------------------------

    if is_math_expression(user_message):

        print("Rule Router -> Calculator")

        return {
            "tool": "calculator",
            "arguments": {
                "expression": user_message
            }
        }

    if is_search_query(user_message):

        print("Rule Router -> Search")

        return {
            "tool": "search",
            "arguments": {
                "query": user_message
            }
        }

    # -----------------------------
    # Fall back to Gemini
    # -----------------------------

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