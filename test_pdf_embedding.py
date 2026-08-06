from backend.documents.pdf_service import extract_text_from_pdf
from backend.documents.chunking import split_text
from backend.embeddings.embedding_service import create_embedding

text = extract_text_from_pdf("sample.pdf")

chunks = split_text(text)

print(f"Total Chunks: {len(chunks)}\n")

for i, chunk in enumerate(chunks):
    embedding = create_embedding(chunk)

    print(f"Chunk {i+1}")
    print(f"Length: {len(chunk)} characters")
    print(f"Embedding Dimension: {len(embedding)}")
    print("-" * 50)