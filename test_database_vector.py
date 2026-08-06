from backend.services.note_service import get_notes
from backend.embeddings.vector_store import (
    build_index,
    search_documents
)

notes = get_notes()

build_index(notes)

results = search_documents(
    "Which framework are we using?"
)

for result in results:
    print(result)