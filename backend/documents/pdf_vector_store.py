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


def _save_index():
    global pdf_index, pdf_chunks

    if pdf_index is not None:
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


def build_pdf_index(
    chunks,
    filename,
    conversation_id
):
    """
    Add PDF chunks to the persistent global FAISS index.

    Every chunk stores its conversation_id so retrieval can
    later restrict results to the current conversation.
    """

    global pdf_chunks, pdf_index

    if not chunks:
        return

    # --------------------------------------------------------
    # Ensure existing index and metadata are loaded together
    # --------------------------------------------------------

    if pdf_index is None:
        load_pdf_index()

    # --------------------------------------------------------
    # Create metadata for this PDF
    # --------------------------------------------------------

    new_chunks = []

    for i, chunk in enumerate(chunks, start=1):
        new_chunks.append({
            "conversation_id": conversation_id,
            "filename": filename,
            "chunk_id": i,
            "chunk": chunk,
        })

    # --------------------------------------------------------
    # Create embeddings
    # --------------------------------------------------------

    embeddings = [
        create_embedding(item["chunk"])
        for item in new_chunks
    ]

    embeddings = np.array(
        embeddings,
        dtype="float32"
    )

    if len(embeddings) == 0:
        return

    # --------------------------------------------------------
    # Create FAISS index if one does not exist
    # --------------------------------------------------------

    if pdf_index is None:
        dimension = embeddings.shape[1]

        pdf_index = faiss.IndexFlatL2(
            dimension
        )

    # --------------------------------------------------------
    # Append embeddings
    # --------------------------------------------------------

    pdf_index.add(embeddings)

    # --------------------------------------------------------
    # Append metadata
    # --------------------------------------------------------

    pdf_chunks.extend(new_chunks)

    # --------------------------------------------------------
    # Save
    # --------------------------------------------------------

    _save_index()

    print(
        f"PDF index updated successfully: "
        f"{len(new_chunks)} chunks from {filename} "
        f"for conversation {conversation_id}"
    )
def validate_pdf_index():
    global pdf_index, pdf_chunks

    if pdf_index is None:
        return False

    if pdf_index.ntotal != len(pdf_chunks):
        print(
            "WARNING: PDF index mismatch:",
            f"FAISS vectors={pdf_index.ntotal},",
            f"metadata chunks={len(pdf_chunks)}"
        )
        return False

    return True

def search_pdf(
    query,
    conversation_id,
    k=5
):
    """
    Search PDF chunks belonging only to the specified
    conversation.
    """

    global pdf_chunks, pdf_index

    if pdf_index is None or not pdf_chunks:
        load_pdf_index()

    if pdf_index is None or not pdf_chunks:
        return []

    # --------------------------------------------------------
    # Create query embedding
    # --------------------------------------------------------

    query_embedding = create_embedding(query)

    query_embedding = np.array(
        [query_embedding],
        dtype="float32"
    )

    # --------------------------------------------------------
    # Search more candidates than requested because the
    # first FAISS results may belong to other conversations.
    # --------------------------------------------------------

    search_k = min(
        max(k * 10, 50),
        len(pdf_chunks)
    )

    _, indices = pdf_index.search(
        query_embedding,
        search_k
    )

    results = []

    for index in indices[0]:

        if index < 0:
            continue

        if index >= len(pdf_chunks):
            continue

        item = pdf_chunks[index]

        # ----------------------------------------------------
        # Conversation isolation
        # ----------------------------------------------------

        if item.get("conversation_id") != conversation_id:
            continue

        results.append({
            "conversation_id": item.get(
                "conversation_id"
            ),
            "filename": item["filename"],
            "chunk_id": item["chunk_id"],
            "chunk": item["chunk"],
        })

        if len(results) >= k:
            break

    return results


def load_pdf_index():
    global pdf_index, pdf_chunks

    if not PDF_INDEX_PATH.exists():
        pdf_index = None
        pdf_chunks = []

        print("No saved PDF index found.")
        return

    try:
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

        else:
            pdf_chunks = []

        print(
            f"PDF FAISS index loaded successfully: "
            f"{len(pdf_chunks)} chunks"
        )
        validate_pdf_index()
    except Exception as e:

        print(
            "Failed to load PDF FAISS index:",
            e
        )

        pdf_index = None
        pdf_chunks = []


def remove_pdf_chunks(filename, conversation_id):
    """
    Remove all chunks belonging to a specific PDF and conversation
    from the persistent FAISS index and metadata.
    """

    global pdf_chunks, pdf_index

    if pdf_index is None:
        load_pdf_index()

    if pdf_index is None or not pdf_chunks:
        return 0

    # Find metadata entries that should be removed
    remove_indices = [
        i
        for i, item in enumerate(pdf_chunks)
        if item.get("filename") == filename
        and item.get("conversation_id") == conversation_id
    ]

    if not remove_indices:
        return 0

    remove_set = set(remove_indices)

    # Keep all metadata except the selected entries
    remaining_chunks = [
        item
        for i, item in enumerate(pdf_chunks)
        if i not in remove_set
    ]

    # Rebuild FAISS index from remaining chunks
    if remaining_chunks:
        embeddings = np.array(
            [
                create_embedding(item["chunk"])
                for item in remaining_chunks
            ],
            dtype="float32"
        )

        dimension = embeddings.shape[1]

        new_index = faiss.IndexFlatL2(dimension)
        new_index.add(embeddings)

        pdf_index = new_index
    else:
        pdf_index = None

    pdf_chunks = remaining_chunks

    _save_index()

    print(
        f"Removed {len(remove_indices)} PDF chunks "
        f"from {filename} for conversation {conversation_id}"
    )

    return len(remove_indices)