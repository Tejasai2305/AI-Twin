"""
Personal Timeline (Feature 7).

Grounding rule, same as the knowledge graph: every timeline entry is
derived from a real, timestamped row already in the database. Nothing
is invented or inferred - no guessing at "milestones" from free text.

Sources merged into one chronological feed:
  - conversations created      (category: "conversation")
  - documents/PDFs uploaded    (category: "document")
  - memories learned           (category: <memory_type>, event: "learned")
  - contradictions resolved    (category: <memory_type>, event: "updated")

Computed on demand (same reasoning as graph_service.py: a persisted
timeline table would be a second copy of the same facts that could
drift out of sync every time a memory/conversation/document changes).

Isolation: user_id=None means "unowned/legacy rows only" (never
"everyone's timeline"), matching every other service in the app.
"""

from backend.database.database import get_connection


def get_timeline(year=None, category=None, limit=200, user_id=None):
    conn = get_connection()
    cursor = conn.cursor()

    owner_clause = "user_id = ?" if user_id is not None else "user_id IS NULL"
    owner_param = (user_id,) if user_id is not None else ()

    events = []

    # --- Conversations started ---
    cursor.execute(
        f"SELECT id, title, created_at FROM conversations WHERE {owner_clause}",
        owner_param,
    )
    for row in cursor.fetchall():
        events.append({
            "date": row[2],
            "type": "conversation",
            "category": "conversation",
            "title": f"Started conversation: {row[1]}",
            "source": "conversation",
            "source_id": row[0],
        })

    # --- Documents uploaded (inherits isolation from their conversation) ---
    cursor.execute(
        f"""
        SELECT a.id, a.filename, a.conversation_id, a.created_at
        FROM attachments a
        LEFT JOIN conversations c ON c.id = a.conversation_id
        WHERE c.{owner_clause}
        """,
        owner_param,
    )
    for row in cursor.fetchall():
        events.append({
            "date": row[3],
            "type": "document",
            "category": "document",
            "title": f"Uploaded document: {row[1]}",
            "source": "document",
            "source_id": row[0],
            "conversation_id": row[2],
        })

    # --- Memories learned (only the earliest/original fact per subject,
    #     not every superseded intermediate row, to avoid double-counting
    #     the same underlying fact as multiple "learned" events) ---
    cursor.execute(
        f"""
        SELECT id, memory, memory_type, confidence, source, created_at
        FROM memories
        WHERE supersedes_id IS NULL AND {owner_clause}
        """,
        owner_param,
    )
    for row in cursor.fetchall():
        events.append({
            "date": row[5],
            "type": "memory",
            "category": row[2] or "other",
            "title": row[1],
            "confidence": row[3],
            "source": row[4],
            "source_id": row[0],
        })

    # --- Contradictions resolved (fact changed over time) ---
    cursor.execute(
        f"""
        SELECT h.memory_id, h.old_memory, h.new_memory, h.changed_at, m.memory_type
        FROM memory_history h
        LEFT JOIN memories m ON m.id = h.memory_id
        WHERE h.action = 'contradiction_resolved' AND m.{owner_clause}
        """,
        owner_param,
    )
    for row in cursor.fetchall():
        events.append({
            "date": row[3],
            "type": "update",
            "category": row[4] or "other",
            "title": f"Updated: \"{row[1]}\" -> \"{row[2]}\"",
            "source": "contradiction",
            "source_id": row[0],
        })

    conn.close()

    # Filter
    if category:
        events = [e for e in events if e["category"] == category]

    if year:
        events = [e for e in events if e["date"] and str(e["date"]).startswith(str(year))]

    # Sort newest first
    events.sort(key=lambda e: e["date"] or "", reverse=True)

    return events[:limit]


def get_timeline_years(user_id=None):
    """Distinct years that have at least one event, for the year filter dropdown."""
    events = get_timeline(limit=10000, user_id=user_id)
    years = sorted(
        {str(e["date"])[:4] for e in events if e["date"]},
        reverse=True,
    )
    return years


def get_timeline_categories(user_id=None):
    events = get_timeline(limit=10000, user_id=user_id)
    return sorted({e["category"] for e in events})
