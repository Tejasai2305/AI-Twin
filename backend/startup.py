from backend.services.note_service import get_notes
from backend.embeddings.vector_store import build_index
from backend.documents.pdf_vector_store import load_pdf_index


def initialize():
    notes = get_notes()
    build_index(notes)

    load_pdf_index()

    print(f"Loaded {len(notes)} notes into FAISS.")