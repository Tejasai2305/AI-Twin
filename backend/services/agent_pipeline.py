from backend.agent.controller import process_request


def process_chat(question):
    """
    Main AI pipeline.
    """

    # -----------------------------
    # Tool Check
    # -----------------------------
    tool_result = process_request(question.question)

    if tool_result is not None and tool_result["success"]:

        return {
            "handled": True,
            "response": {
                "question": question.question,
                "answer": tool_result["result"],
                "mode": "tool",
                "sources": [],
            },
        }

    return {
        "handled": False,
    }