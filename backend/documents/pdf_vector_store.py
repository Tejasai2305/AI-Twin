import faiss
import os
import json
import numpy as np
from pathlib import Path

from backend.embeddings.embedding_service import create_embedding


BASE_DIR = Path(__file__).resolve().parent.parent.parent

DATA_DIR = Path(
    os.getenv("AI_TWIN_DATA_DIR", str(BASE_DIR))
)

DATA_DIR.mkdir(parents=True, exist_ok=True)

PDF_INDEX_PATH = DATA_DIR / "pdf_index.faiss"
PDF_CHUNKS_PATH = DATA_DIR / "pdf_chunks.json"

pdf_chunks = []
pdf_index = None


def build_pdf_index(chunks, filename):
    global pdf_chunks, pdf_index

    # Create fresh index for the uploaded PDF
    chunk_data = []

    for i, chunk in enumerate(chunks, start=1):
        chunk_data.append({
            "filename": filename,
            "chunk_id": i,
            "chunk": chunk
        })

    pdf_chunks = chunk_data

    embeddings = [
        create_embedding(item["chunk"])
        for item in pdf_chunks
    ]

    embeddings = np.array(embeddings).astype("float32")

    if len(embeddings) == 0:
        pdf_index = None
        return

    dimension = embeddings.shape[1]

    # Always create a fresh FAISS index
    pdf_index = faiss.IndexFlatL2(dimension)

    pdf_index.add(embeddings)

    faiss.write_index(
        pdf_index,
        str(PDF_INDEX_PATH)
    )

    with open(PDF_CHUNKS_PATH, "w", encoding="utf-8") as f:
        json.dump(
            pdf_chunks,
            f,
            indent=4,
            ensure_ascii=False
        )

    print(
        f"PDF index built successfully: "
        f"{len(pdf_chunks)} chunks from {filename}"
    )

def search_pdf(query, k=5):
    global pdf_chunks, pdf_index

    if pdf_index is None or not pdf_chunks:
        load_pdf_index()

    if pdf_index is None or not pdf_chunks:
        return []

    query_embedding = create_embedding(query)

    query_embedding = np.array(
        [query_embedding]
    ).astype("float32")

    k = min(k, len(pdf_chunks))

    _, indices = pdf_index.search(
        query_embedding,
        k
    )

    results = []

    for index in indices[0]:

        if index < 0:
            continue

        if index < len(pdf_chunks):

            results.append({
                "filename": pdf_chunks[index]["filename"],
                "chunk_id": pdf_chunks[index]["chunk_id"],
                "chunk": pdf_chunks[index]["chunk"]
            })

    return results


def load_pdf_index():
    global pdf_index, pdf_chunks

    if PDF_INDEX_PATH.exists():

        pdf_index = faiss.read_index(
            str(PDF_INDEX_PATH)
        )

        if PDF_CHUNKS_PATH.exists():

            with open(
                PDF_CHUNKS_PATH,
                "r",
                encoding="utf-8"
            ) as f:

                pdf_chunks = json.load(f)

        print(
            f"PDF FAISS index loaded successfully: "
            f"{len(pdf_chunks)} chunks"
        )

    else:

        pdf_index = None
        pdf_chunks = []

        print("No saved PDF index found.")