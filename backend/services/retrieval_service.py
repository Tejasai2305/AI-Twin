from backend.services import note_service
from backend.documents.pdf_vector_store import search_pdf


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

    notes = note_service.search_notes(question)

    for note in notes:
        notes_text += (
            f"Title: {note['title']}\n"
            f"Content: {note['content']}\n\n"
        )

    pdf_results = search_pdf(question)

    print("\n========== NOTE RETRIEVAL ==========")
    print("Question:", question)
    print("Notes found:", notes)
    print("PDF results:", pdf_results)
    print("====================================\n")

    for result in pdf_results:
        pdf_text += (
            f"PDF: {result['filename']}\n"
            f"Content: {result['chunk']}\n\n"
        )

    return notes_text, pdf_text, pdf_results