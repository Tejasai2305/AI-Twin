"""
Document Center (Feature 13 / 19).

Builds document listing + metadata on top of the existing,
already-working PDF upload/index pipeline (documents/upload.py,
pdf_vector_store.py). Nothing about extraction/chunking/indexing is
changed here - this only adds visibility (list, status, chunk count)
and a real delete path using the removal function that already
existed in pdf_vector_store.py but was never wired to an endpoint.

Documents don't have their own owner column - they inherit isolation
from the conversation they were uploaded into (attachments.
conversation_id -> conversations.user_id), same convention as
memories: user_id=None means "unowned/legacy only", never "everyone's
documents".
"""

import os
from pathlib import Path

from backend.database.database import get_connection
from backend.documents.pdf_vector_store import get_chunk_count, remove_pdf_chunks


def list_documents(conversation_id=None, user_id=None):
    conn = get_connection()
    cursor = conn.cursor()

    clauses = []
    params = []

    if conversation_id is not None:
        clauses.append("a.conversation_id = ?")
        params.append(conversation_id)

    if user_id is not None:
        clauses.append("c.user_id = ?")
        params.append(user_id)
    else:
        clauses.append("c.user_id IS NULL")

    where_clause = f"WHERE {' AND '.join(clauses)}" if clauses else ""

    cursor.execute(
        f"""
        SELECT a.id, a.conversation_id, a.filename, a.file_path, a.file_type, a.created_at
        FROM attachments a
        LEFT JOIN conversations c ON c.id = a.conversation_id
        {where_clause}
        ORDER BY a.created_at DESC
        """,
        params,
    )

    rows = cursor.fetchall()
    conn.close()

    documents = []
    for row in rows:
        attachment_id, conv_id, filename, file_path, file_type, created_at = row
        chunk_count = get_chunk_count(filename, conv_id)
        documents.append({
            "id": attachment_id,
            "conversation_id": conv_id,
            "filename": filename,
            "file_type": file_type,
            "created_at": created_at,
            "chunk_count": chunk_count,
            "indexed": chunk_count > 0,
            "file_exists": Path(file_path).exists(),
        })

    return documents


def get_document(attachment_id):
    """
    Returns the document plus the user_id that owns its conversation
    (owner_user_id), so callers can do their own ownership check -
    same pattern as memory_service.get_memory_detail() /
    routers/memory.py's _assert_owned.
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT a.id, a.conversation_id, a.filename, a.file_path, a.file_type,
               a.created_at, c.user_id
        FROM attachments a
        LEFT JOIN conversations c ON c.id = a.conversation_id
        WHERE a.id = ?
        """,
        (attachment_id,),
    )

    row = cursor.fetchone()
    conn.close()

    if row is None:
        return None

    attachment_id, conv_id, filename, file_path, file_type, created_at, owner_user_id = row
    chunk_count = get_chunk_count(filename, conv_id)

    return {
        "id": attachment_id,
        "conversation_id": conv_id,
        "filename": filename,
        "file_type": file_type,
        "created_at": created_at,
        "chunk_count": chunk_count,
        "indexed": chunk_count > 0,
        "file_exists": Path(file_path).exists(),
        "owner_user_id": owner_user_id,
    }


def delete_document(attachment_id):
    """
    Removes the attachment record, its FAISS chunks, and the file on
    disk. Returns the deleted document's summary, or None if it
    didn't exist - so a stale/deleted document can never be
    accidentally retrieved from the index afterward (Feature 27).
    """
    doc = get_document(attachment_id)

    if doc is None:
        return None

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT file_path FROM attachments WHERE id = ?",
        (attachment_id,),
    )
    row = cursor.fetchone()
    file_path = row[0] if row else None

    cursor.execute("DELETE FROM attachments WHERE id = ?", (attachment_id,))
    conn.commit()
    conn.close()

    remove_pdf_chunks(doc["filename"], doc["conversation_id"])

    if file_path and os.path.exists(file_path):
        try:
            os.remove(file_path)
        except OSError as e:
            print("Could not remove document file from disk:", e)

    return doc
