def classify_question(question: str) -> str:
    """
    Returns one of:
    - conversation
    - knowledge
    - hybrid
    """

    question = question.lower().strip()

    # --------------------------------------------------
    # Document-specific questions get highest priority
    # --------------------------------------------------

    knowledge_keywords = [
        "resume",
        "project",
        "internship",
        "skill",
        "skills",
        "cgpa",
        "education",
        "experience",
        "pdf",
        "document",
        "uploaded",
        "uploaded document",
        "uploaded pdf",
        "current document",
        "current pdf",
        "according to the document",
        "according to the pdf",
        "mentioned in the document",
        "mentioned in the pdf",
        "in the document",
        "in the pdf",
        "from the document",
        "from the pdf",
        "aqivision",
        "technical skills",
    ]

    for keyword in knowledge_keywords:
        if keyword in question:
            return "knowledge"

    # --------------------------------------------------
    # Conversation-specific questions
    # --------------------------------------------------

    conversation_keywords = [
        "what did i say",
        "previous message",
        "previous question",
        "this conversation",
        "our conversation",
        "summarize this chat",
        "what was my last",
        "remember",
        "earlier",
        "my favorite",
        "my preference",
        "my preferred",
        "i prefer",
        "do i prefer",
        "what do i prefer",

    ]

    for keyword in conversation_keywords:
        if keyword in question:
            return "conversation"

    # --------------------------------------------------
    # Default
    # --------------------------------------------------

    return "hybrid"