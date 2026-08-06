def classify_question(question: str) -> str:
    """
    Returns one of:
    - conversation
    - knowledge
    - hybrid
    """

    question = question.lower()

    conversation_keywords = [
        "my name",
        "what did i say",
        "previous message",
        "previous question",
        "this conversation",
        "our conversation",
        "summarize this chat",
        "what was my last",
        "remember",
        "earlier"
    ]

    knowledge_keywords = [
        "resume",
        "project",
        "internship",
        "skill",
        "cgpa",
        "education",
        "experience",
        "pdf",
        "notes",
        "aqivision"
    ]

    for keyword in conversation_keywords:
        if keyword in question:
            return "conversation"

    for keyword in knowledge_keywords:
        if keyword in question:
            return "knowledge"

    return "hybrid"