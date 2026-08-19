from backend.services import note_service
from backend.documents.pdf_vector_store import search_pdf


def build_pdf_queries(question: str):
    """
    Build multiple targeted PDF queries for complex questions.
    """

    queries = [question]

    q = question.lower()

    # Team members / student IDs
    if any(word in q for word in [
        "team",
        "member",
        "members",
        "student id",
        "student ids",
        "students",
        "names",
    ]):
        queries.append(
            "List all project team members with their names and student IDs"
        )

    # Supervisor
    if any(word in q for word in [
        "supervisor",
        "guide",
        "project supervisor",
        "project guide",
    ]):
        queries.append(
            "Who is the project supervisor or project guide?"
        )

    # Project title
    if any(word in q for word in [
        "title",
        "project title",
        "name of the project",
    ]):
        queries.append(
            "What is the exact title of the project?"
        )

    # Microcontroller
    if any(word in q for word in [
        "microcontroller",
        "controller",
        "esp32",
        "processor",
    ]):
        queries.append(
            "Which microcontroller or controller is used in the project?"
        )

    # Remove duplicate queries
    return list(dict.fromkeys(queries))


def retrieve_context(mode: str, question: str):
    """
    Returns:
        notes_text, pdf_text, pdf_results
    """

    notes_text = ""
    pdf_text = ""
    pdf_results = []

    if mode not in ["knowledge", "hybrid"]:
        return notes_text, pdf_text, pdf_results

    # -----------------------------
    # NOTE RETRIEVAL
    # -----------------------------

    notes = note_service.search_notes(question)

    for note in notes:
        notes_text += (
            f"Title: {note['title']}\n"
            f"Content: {note['content']}\n\n"
        )

    # -----------------------------
    # PDF RETRIEVAL
    # -----------------------------

    pdf_queries = build_pdf_queries(question)

    seen_chunks = set()

    for query in pdf_queries:

        results = search_pdf(query, k=5)

        for result in results:

            chunk_key = (
                result["filename"],
                result["chunk_id"]
            )

            if chunk_key in seen_chunks:
                continue

            seen_chunks.add(chunk_key)
            pdf_results.append(result)

    print("\n========== NOTE RETRIEVAL ==========")
    print("Question:", question)
    print("Notes found:", notes)
    print("PDF queries:", pdf_queries)
    print("PDF results:", pdf_results)
    print("====================================\n")

    # -----------------------------
    # BUILD PDF CONTEXT
    # -----------------------------

    for result in pdf_results:
        pdf_text += (
            f"PDF: {result['filename']}\n"
            f"Chunk ID: {result['chunk_id']}\n"
            f"Content: {result['chunk']}\n\n"
        )

    return notes_text, pdf_text, pdf_results