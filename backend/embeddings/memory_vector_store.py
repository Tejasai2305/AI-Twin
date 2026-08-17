import faiss
import numpy as np
import pickle
from pathlib import Path

from backend.embeddings.embedding_service import (
    create_embedding,
    EMBEDDING_DIMENSION,
)


BASE_DIR = Path(__file__).resolve().parent.parent.parent

INDEX_PATH = BASE_DIR / "memory.index"
MEMORY_PATH = BASE_DIR / "memory.pkl"

index = faiss.IndexFlatL2(EMBEDDING_DIMENSION)
memory_list = []


def build_memory_index(memories):
    global index, memory_list

    index = faiss.IndexFlatL2(EMBEDDING_DIMENSION)
    memory_list = []

    if not memories:
        return

    texts = [memory for _, memory, _ in memories]

    embeddings = np.array(
        [create_embedding(text) for text in texts],
        dtype="float32",
    )

    index.add(embeddings)

    memory_list = texts

    print("Memory index rebuilt.")
    print("Indexed memories:", memory_list)

    faiss.write_index(index, str(INDEX_PATH))

    with open(MEMORY_PATH, "wb") as f:
        pickle.dump(memory_list, f)


def load_memory_index():
    global index, memory_list

    if INDEX_PATH.exists():
        index = faiss.read_index(str(INDEX_PATH))

    if MEMORY_PATH.exists():
        with open(MEMORY_PATH, "rb") as f:
            memory_list = pickle.load(f)


def search_memory(query, top_k=3, threshold=1.0):
    print("Searching memory for:", query)

    if len(memory_list) == 0:
        load_memory_index()

    if len(memory_list) == 0:
        return []

    query_embedding = np.array(
        [create_embedding(query)],
        dtype="float32",
    )

    distances, indices = index.search(query_embedding, top_k)

    results = []

    for distance, idx in zip(distances[0], indices[0]):
        if idx < len(memory_list) and distance <= threshold:
            results.append(memory_list[idx])

    print("Memory search results:", results)

    return results