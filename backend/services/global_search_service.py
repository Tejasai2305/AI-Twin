"""
Global Search (Feature 14).

Searches across everything the user actually has stored, deliberately
crossing conversation boundaries (unlike PDF retrieval during chat,
which stays conversation-isolated for grounding reasons) - this is
the user searching their own data, not the AI answering a document
question. It still must never cross between different USERS' data
though: user_id=None means "search only unowned/legacy data", never
"search everyone's data", matching every other service in the app.

Sources searched:
  - conversation titles + message content (reuses existing schema)
  - active memories (substring match on the stored fact text)
  - documents: filename, and indexed PDF chunk content

Returned as categorized results rather than one flat list, per the
brief's "provide categorized search results".
"""

from backend.database.database import get_connection
from backend.services.memory_service import get_memories_detailed
from backend.documents import pdf_vector_store


def global_search(query, limit_per_category=10, user_id=None):
    query = (query or "").strip()

    if not query:
        return {"conversations": [], "memories": [], "documents": [], "query": query}

    lowered = query.lower()
    owner_clause = "user_id = ?" if user_id is not None else "user_id IS NULL"
    owner_param = (user_id,) if user_id is not None else ()

    # ---------------- Conversations ----------------
    conn = get_connection()
    cursor = conn.cursor()

    pattern = f"%{query}%"
    cursor.execute(
        f"""
        SELECT c.id, c.title, c.created_at, m.content
        FROM conversations AS c
        LEFT JOIN messages AS m ON c.id = m.conversation_id
        WHERE (c.title LIKE ? OR m.content LIKE ?) AND c.{owner_clause}
        ORDER BY c.created_at DESC
        """,
        (pattern, pattern) + owner_param,
    )
    rows = cursor.fetchall()

    seen_conv = set()
    conversation_results = []
    accessible_conversation_ids = set()
    for conv_id, title, created_at, content in rows:
        accessible_conversation_ids.add(conv_id)
        if conv_id in seen_conv:
            continue
        seen_conv.add(conv_id)
        matched_message = content if content and lowered in content.lower() else None
        conversation_results.append({
            "conversation_id": conv_id,
            "title": title,
            "created_at": created_at,
            "matched_message": matched_message,
        })
        if len(conversation_results) >= limit_per_category:
            break

    # Full set of conversation ids this user can see, regardless of
    # whether they matched the query text - needed below to scope
    # document search to only this user's conversations.
    cursor.execute(f"SELECT id FROM conversations WHERE {owner_clause}", owner_param)
    owned_conversation_ids = {row[0] for row in cursor.fetchall()}
    conn.close()

    # ---------------- Memories ----------------
    memories = get_memories_detailed(include_inactive=False, user_id=user_id)
    memory_results = [
        {
            "id": m["id"],
            "memory": m["memory"],
            "memory_type": m["memory_type"],
            "confidence": m["confidence"],
        }
        for m in memories
        if lowered in m["memory"].lower()
    ][:limit_per_category]

    # ---------------- Documents ----------------
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        f"""
        SELECT a.id, a.conversation_id, a.filename, a.created_at
        FROM attachments a
        LEFT JOIN conversations c ON c.id = a.conversation_id
        WHERE a.filename LIKE ? AND c.{owner_clause}
        """,
        (pattern,) + owner_param,
    )
    filename_matches = cursor.fetchall()
    conn.close()

    document_results = {}
    for doc_id, conv_id, filename, created_at in filename_matches:
        document_results[filename] = {
            "attachment_id": doc_id,
            "conversation_id": conv_id,
            "filename": filename,
            "created_at": created_at,
            "matched_chunk": None,
        }

    # Also search indexed chunk content, scoped to this user's own
    # conversations only.
    if pdf_vector_store.pdf_chunks is None or len(pdf_vector_store.pdf_chunks) == 0:
        pdf_vector_store.load_pdf_index()

    for chunk in (pdf_vector_store.pdf_chunks or []):
        if chunk.get("conversation_id") not in owned_conversation_ids:
            continue
        if lowered in chunk.get("chunk", "").lower():
            filename = chunk["filename"]
            if filename not in document_results:
                document_results[filename] = {
                    "attachment_id": None,
                    "conversation_id": chunk.get("conversation_id"),
                    "filename": filename,
                    "created_at": None,
                    "matched_chunk": chunk["chunk"][:200],
                }
            elif document_results[filename]["matched_chunk"] is None:
                document_results[filename]["matched_chunk"] = chunk["chunk"][:200]

    return {
        "query": query,
        "conversations": conversation_results,
        "memories": memory_results,
        "documents": list(document_results.values())[:limit_per_category],
    }
