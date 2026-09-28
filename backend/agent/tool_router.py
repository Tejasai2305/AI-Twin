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


def is_document_query(text: str) -> bool:
    """
    Detect questions that should be answered from uploaded
    documents such as resumes, PDFs, reports, etc.

    Document questions must NOT be sent to the web search tool.
    """

    text = text.lower().strip()

    document_keywords = [
        "resume",
        "cv",
        "curriculum vitae",
        "pdf",
        "document",
        "uploaded document",
        "uploaded pdf",
        "my resume",
        "my cv",
        "according to my resume",
        "according to the resume",
        "according to my cv",
        "according to the document",
        "according to the pdf",
        "in my resume",
        "in the resume",
        "from my resume",
        "from the resume",
        "mentioned in my resume",
        "mentioned in the resume",
        "listed in my resume",
        "listed in the resume",
    ]

    return any(
        keyword in text
        for keyword in document_keywords
    )


def is_search_query(text: str) -> bool:
    """
    Detect requests that clearly need web search.

    Important:
    Document/resume questions are excluded before this function
    is used by detect_tool().
    """

    text = text.lower().strip()

    keywords = [
        "latest",
        "news",
        "today",
        "recent",
        "search",
        "lookup",
        "find on internet",
        "web",
        "online",
        "internet",
    ]

    return any(
        keyword in text
        for keyword in keywords
    )


def detect_tool(user_message: str):
    """
    Hybrid Tool Router.

    Priority:
    1. Document questions -> no external tool
    2. Calculator
    3. Web search
    4. Gemini tool classification
    """

    # --------------------------------------------------
    # DOCUMENT QUESTIONS
    # --------------------------------------------------
    # These must be handled by the document/PDF retrieval
    # pipeline, not by the web search tool.
    # --------------------------------------------------

    if is_document_query(user_message):

        print("Tool Router -> Document Retrieval")

        return None

    # --------------------------------------------------
    # FAST RULE-BASED ROUTING
    # --------------------------------------------------

    if is_math_expression(user_message):

        print("Rule Router -> Calculator")

        return {
            "tool": "calculator",
            "arguments": {
                "expression": user_message
            }
        }

    # --------------------------------------------------
    # WEB SEARCH
    # --------------------------------------------------

    if is_search_query(user_message):

        print("Rule Router -> Search")

        return {
            "tool": "search",
            "arguments": {
                "query": user_message
            }
        }

    # --------------------------------------------------
    # FALL BACK TO GEMINI
    # --------------------------------------------------

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

    # --------------------------------------------------
    # VALIDATION
    # --------------------------------------------------

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