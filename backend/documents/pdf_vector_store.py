import faiss
import os
import json
import numpy as np
from backend.embeddings.embedding_service import create_embedding

pdf_chunks = []
pdf_index = None


def build_pdf_index(chunks, filename):
    global pdf_chunks, pdf_index

    chunk_data = []

    for i, chunk in enumerate(chunks, start=1):
        chunk_data.append({
            "filename": filename,
            "chunk_id": i,
            "chunk": chunk
        })

    pdf_chunks.extend(chunk_data)

    embeddings = [create_embedding(item["chunk"]) for item in chunk_data]
    embeddings = np.array(embeddings).astype("float32")

    dimension = embeddings.shape[1]

    if pdf_index is None:
        pdf_index = faiss.IndexFlatL2(dimension)
    elif pdf_index.d != dimension:
        raise ValueError(
            f"Embedding dimension mismatch: expected {pdf_index.d}, got {dimension}"
        )

    pdf_index.add(embeddings)

    faiss.write_index(pdf_index, "pdf_index.faiss")

    with open("pdf_chunks.json", "w") as f:
        json.dump(pdf_chunks, f, indent=4)

def search_pdf(query, k=3):
    global pdf_chunks, pdf_index

    if pdf_index is None:
        return []

    query_embedding = create_embedding(query)
    query_embedding = np.array([query_embedding]).astype("float32")

    _, indices = pdf_index.search(query_embedding, k)

    results = []

    for index in indices[0]:
        if index < len(pdf_chunks):
            results.append({
    "filename": pdf_chunks[index]["filename"],
    "chunk_id": pdf_chunks[index]["chunk_id"],
    "chunk": pdf_chunks[index]["chunk"]
})

    return results
def load_pdf_index():
    global pdf_index, pdf_chunks

    if os.path.exists("pdf_index.faiss"):
        pdf_index = faiss.read_index("pdf_index.faiss")

        if os.path.exists("pdf_chunks.json"):
            with open("pdf_chunks.json", "r") as f:
                pdf_chunks = json.load(f)

        print("PDF FAISS index loaded successfully.")
    else:
        print("No saved PDF index found.")