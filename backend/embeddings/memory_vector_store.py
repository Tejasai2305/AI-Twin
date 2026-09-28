import faiss
import json
import os
import numpy as np
from pathlib import Path

from backend.embeddings.embedding_service import (
    create_embedding,
    EMBEDDING_DIMENSION,
)


BASE_DIR = Path(__file__).resolve().parent.parent.parent

DATA_DIR = Path(
    os.getenv("AI_TWIN_DATA_DIR", str(BASE_DIR))
)

DATA_DIR.mkdir(parents=True, exist_ok=True)

INDEX_PATH = DATA_DIR / "memory.index"
MEMORY_PATH = DATA_DIR / "memory.json"
_LEGACY_MEMORY_PATH = DATA_DIR / "memory.pkl"

index = faiss.IndexFlatL2(EMBEDDING_DIMENSION)
memory_list = []


def build_memory_index(memories):
    """
    memories: iterable of (id, memory, importance, user_id) rows -
    every active memory across every user, each tagged with its
    owner so search_memory() can filter results per-user.
    """
    global index, memory_list

    index = faiss.IndexFlatL2(EMBEDDING_DIMENSION)
    memory_list = []

    if not memories:
        return

    entries = [
        {"memory": row[1], "user_id": row[3] if len(row) > 3 else None}
        for row in memories
    ]

    texts = [e["memory"] for e in entries]

    embeddings = np.array(
        [create_embedding(text) for text in texts],
        dtype="float32",
    )

    index.add(embeddings)

    memory_list = entries

    print("Memory index rebuilt.")
    print("Indexed memories:", [e["memory"] for e in memory_list])

    faiss.write_index(index, str(INDEX_PATH))

    with open(MEMORY_PATH, "w", encoding="utf-8") as f:
        json.dump(memory_list, f, ensure_ascii=False)


def load_memory_index():
    global index, memory_list

    if INDEX_PATH.exists():
        index = faiss.read_index(str(INDEX_PATH))

    if MEMORY_PATH.exists():
        with open(MEMORY_PATH, "r", encoding="utf-8") as f:
            memory_list = json.load(f)
    elif _LEGACY_MEMORY_PATH.exists():
        # One-time migration from the old pickle format, if present
        # from before this fix. Read once, then re-save as JSON so
        # pickle is never touched again on subsequent loads.
        import pickle  # local import: only ever needed for this
        # one-time legacy migration path, never for normal operation.
        with open(_LEGACY_MEMORY_PATH, "rb") as f:
            memory_list = pickle.load(f)
        with open(MEMORY_PATH, "w", encoding="utf-8") as f:
            json.dump(memory_list, f, ensure_ascii=False)
        print("Migrated memory.pkl to memory.json (pickle no longer used).")

    # Older index files (from before per-user tagging) stored a flat
    # list of strings. Normalize those into the {memory, user_id}
    # shape on load so search_memory() always has a consistent
    # contract, without forcing a rebuild just to read an old file.
    if memory_list and isinstance(memory_list[0], str):
        memory_list = [{"memory": text, "user_id": None} for text in memory_list]


def search_memory(query, top_k=3, threshold=1.5, user_id=None):
    print("Searching memory for:", query)

    if len(memory_list) == 0:
        load_memory_index()

    if len(memory_list) == 0:
        return []

    query_embedding = np.array(
        [create_embedding(query)],
        dtype="float32",
    )

    # Retrieve more candidates than we ultimately return, since some
    # will be filtered out below (wrong owner, below threshold, no
    # keyword overlap).
    candidate_k = min(max(top_k * 5, 20), len(memory_list))

    distances, indices = index.search(
        query_embedding,
        candidate_k,
    )

    query_words = set(
        query.lower().replace("?", "").replace(".", "").split()
    )

    # Words that are too generic to help identify a memory.
    stop_words = {
        "what",
        "which",
        "who",
        "where",
        "when",
        "why",
        "how",
        "does",
        "do",
        "did",
        "is",
        "are",
        "the",
        "a",
        "an",
        "my",
        "me",
        "i",
        "user",
        "like",
        "prefer",
        "favorite",
    }

    query_keywords = query_words - stop_words

    scored_results = []

    for distance, idx in zip(distances[0], indices[0]):

        if idx < 0 or idx >= len(memory_list):
            continue

        if distance > threshold:
            continue

        entry = memory_list[idx]

        # Owner isolation: an authenticated user only ever sees their
        # own memories; unauthenticated (no-auth/single-user) mode
        # only sees unowned/legacy memories - matching the exact
        # convention already used for conversations, so behavior is
        # unchanged for any deployment not using auth at all.
        if entry.get("user_id") != user_id:
            continue

        memory = entry["memory"]

        memory_words = set(
            memory.lower().replace("?", "").replace(".", "").split()
        )

        keyword_overlap = len(query_keywords & memory_words)

        if query_keywords and keyword_overlap == 0:
            continue

        score = float(distance) - (keyword_overlap * 0.25)

        scored_results.append(
            (
                score,
                float(distance),
                keyword_overlap,
                memory,
            )
        )

    scored_results.sort(key=lambda x: x[0])

    results = [
        memory
        for _, _, _, memory in scored_results[:top_k]
    ]

    print("Memory search results:", results)

    return results