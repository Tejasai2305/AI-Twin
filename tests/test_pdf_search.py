from backend.documents.pdf_service import extract_text_from_pdf
from backend.documents.chunking import split_text
from backend.documents.pdf_vector_store import (
    build_pdf_index,
    search_pdf,
)


def test_pdf_search():
    pdf_file = "sample.pdf"
    conversation_id = 999999

    text = extract_text_from_pdf(pdf_file)
    chunks = split_text(text)

    assert text
    assert chunks

    build_pdf_index(
        chunks,
        pdf_file,
        conversation_id,
    )

    query = "What programming languages do I know?"

    results = search_pdf(
        query,
        conversation_id=conversation_id,
    )

    assert results
    assert all(
        result["conversation_id"] == conversation_id
        for result in results
    )

    print("\nSearch Results:\n")

    for i, result in enumerate(results, 1):
        print(f"Result {i}")
        print(result)
        print("-" * 60)