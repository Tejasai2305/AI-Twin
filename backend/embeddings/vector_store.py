import faiss
import numpy as np

from backend.embeddings.embedding_service import create_embedding

index = faiss.IndexFlatL2(384)

documents = []


def clear_index():
    global index, documents

    index = faiss.IndexFlatL2(384)
    documents = []


def add_document(title, content):

    text = f"{title}\n{content}"

    embedding = create_embedding(text)

    vector = np.array([embedding], dtype="float32")

    index.add(vector)

    documents.append({
        "title": title,
        "content": content
    })


def build_index(notes):

    clear_index()

    for note in notes:
        add_document(
            note["title"],
            note["content"]
        )


def search_documents(query, k=3):

    if len(documents) == 0:
        return []

    embedding = create_embedding(query)

    vector = np.array([embedding], dtype="float32")

    distances, indices = index.search(vector, k)

    results = []

    for distance, i in zip(distances[0], indices[0]):
        if i < len(documents):
            results.append({
                "title": documents[i]["title"],
                "content": documents[i]["content"],
                "distance": float(distance)
            })

    return results