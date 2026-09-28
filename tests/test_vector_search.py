from backend.embeddings.vector_store import (
    add_document,
    search_documents
)

# Add some sample notes
add_document(
    "FastAPI",
    "FastAPI is a modern Python framework for building APIs."
)

add_document(
    "SQLite",
    "SQLite stores all notes for the AI Twin project."
)

add_document(
    "Football",
    "Football is played with eleven players."
)

# Search
results = search_documents(
    "Which framework are we using?"
)

print(results)