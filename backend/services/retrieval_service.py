from backend.services import note_service
from backend.documents.pdf_vector_store import search_pdf


def build_pdf_queries(question: str):
    """
    Build targeted PDF queries for document retrieval.

    Multiple queries are used for questions where the answer may
    span several document chunks.
    """

    q = question.lower().strip()

    queries = [question]

    # --------------------------------------------------------
    # Resume / project questions
    # --------------------------------------------------------

    project_terms = [
        "project",
        "projects",
        "built",
        "build",
        "worked on",
        "developed",
        "development",
        "listed",
        "mentioned",
    ]

    resume_terms = [
        "resume",
        "cv",
        "curriculum vitae",
    ]

    is_project_question = any(
        term in q for term in project_terms
    )

    is_resume_question = any(
        term in q for term in resume_terms
    )

    if is_project_question and is_resume_question:
        queries.append(
            "What projects did I build according to my resume?"
        )

    elif is_project_question:
        queries.append(
            "projects and project descriptions"
        )

    # --------------------------------------------------------
    # Team members
    # --------------------------------------------------------

    if any(word in q for word in [
        "team",
        "member",
        "members",
        "student id",
        "student ids",
        "students",
    ]):
        queries.append(
            "List all project team members with their names and student IDs"
        )

    # --------------------------------------------------------
    # Supervisor / guide
    # --------------------------------------------------------

    if any(word in q for word in [
        "supervisor",
        "guide",
        "project supervisor",
        "project guide",
    ]):
        queries.append(
            "Who is the project supervisor or project guide?"
        )

    # --------------------------------------------------------
    # Project title
    # --------------------------------------------------------

    if any(word in q for word in [
        "title",
        "project title",
        "name of the project",
    ]):
        queries.append(
            "What is the exact title of the project?"
        )

    # --------------------------------------------------------
    # Microcontroller / hardware
    # --------------------------------------------------------

    if any(word in q for word in [
        "microcontroller",
        "controller",
        "esp32",
        "processor",
    ]):
        queries.append(
            "Which microcontroller or controller is used in the project?"
        )

    # --------------------------------------------------------
    # Skills
    # --------------------------------------------------------

    if any(word in q for word in [
        "skill",
        "skills",
        "technical skill",
        "technical skills",
        "programming language",
        "programming languages",
        "framework",
        "frameworks",
    ]):
        queries.append(
            "technical skills programming languages frameworks libraries"
        )

    # --------------------------------------------------------
    # Internship / experience
    # --------------------------------------------------------

    internship_question = any(
        word in q
        for word in [
            "internship",
            "internships",
            "intern",
            "experience",
            "job",
            "work experience",
        ]
    )

    if internship_question:
        queries.append(
            "internships work experience companies roles dates"
        )

        # For resume questions, explicitly target the complete
        # experience section.
        if is_resume_question:
            queries.extend([
                "Experience Internships",
                "Machine Learning Intern Web Development Intern Frontend Developer Intern",
                "companies roles internship dates experience",
            ])

    # --------------------------------------------------------
    # Education
    # --------------------------------------------------------

    if any(word in q for word in [
        "education",
        "degree",
        "college",
        "university",
        "cgpa",
        "percentage",
        "marks",
    ]):
        queries.append(
            "education degree college CGPA percentage"
        )

    # --------------------------------------------------------
    # Remove duplicates while preserving order
    # --------------------------------------------------------

    return list(dict.fromkeys(queries))


def retrieve_context(
    mode: str,
    question: str,
    conversation_id: int
):
    """
    Retrieve notes and PDF context for the current question.

    PDF retrieval is restricted to the current conversation.
    """

    notes_text = ""
    pdf_text = ""
    pdf_results = []

    # --------------------------------------------------------
    # Only knowledge/hybrid modes require retrieval
    # --------------------------------------------------------

    if mode not in [
        "knowledge",
        "hybrid"
    ]:
        return (
            notes_text,
            pdf_text,
            pdf_results
        )

    # --------------------------------------------------------
    # NOTE RETRIEVAL
    # --------------------------------------------------------

    notes = note_service.search_notes(
        question
    )

    for note in notes:
        notes_text += (
            f"Title: {note['title']}\n"
            f"Content: {note['content']}\n\n"
        )

    # --------------------------------------------------------
    # PDF RETRIEVAL
    # --------------------------------------------------------

    pdf_queries = build_pdf_queries(
        question
    )

    seen_chunks = set()

    for query in pdf_queries:

        results = search_pdf(
            query,
            conversation_id=conversation_id,
            k=3 
        )

        for result in results:

            chunk_key = (
                result["conversation_id"],
                result["filename"],
                result["chunk_id"]
            )

            if chunk_key in seen_chunks:
                continue

            seen_chunks.add(
                chunk_key
            )

            pdf_results.append(
                result
            )

    # --------------------------------------------------------
    # DEBUG OUTPUT
    # --------------------------------------------------------

    print(
        "\n========== NOTE RETRIEVAL =========="
    )

    print(
        "Conversation ID:",
        conversation_id
    )

    print(
        "Question:",
        question
    )

    print(
        "Notes found:",
        notes
    )

    print(
        "PDF queries:",
        pdf_queries
    )

    print(
        "PDF results:",
        pdf_results
    )

    print(
        "====================================\n"
    )

    # --------------------------------------------------------
    # BUILD PDF CONTEXT
    # --------------------------------------------------------

    for result in pdf_results:

        pdf_text += (
            f"PDF: {result['filename']}\n"
            f"Chunk ID: {result['chunk_id']}\n"
            f"Content: {result['chunk']}\n\n"
        )

    return (
        notes_text,
        pdf_text,
        pdf_results
    )
