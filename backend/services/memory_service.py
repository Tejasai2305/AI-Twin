import os
from pathlib import Path
from backend.database.database import get_connection
from backend.embeddings.memory_vector_store import build_memory_index

BASE_DIR = Path(__file__).resolve().parent.parent.parent

DATA_DIR = Path(
    os.getenv("AI_TWIN_DATA_DIR", str(BASE_DIR))
)

DATA_DIR.mkdir(parents=True, exist_ok=True)

DB_NAME = DATA_DIR / "notes.db"

VALID_MEMORY_TYPES = {
    "personal", "education", "career", "technical_skill", "project",
    "preference", "goal", "achievement", "experience", "contact", "other",
}

# Fact types that rarely change once true (used by contradiction handling
# to decide how cautious to be about overwriting).
STABLE_MEMORY_TYPES = {"education", "achievement", "project"}


def _row_to_dict(row):
    """
    Row shape (in column order from SELECT below):
    id, memory, importance, memory_type, source, source_reference,
    confidence, evidence, is_active, valid_from, valid_until,
    created_at, updated_at, supersedes_id, user_id
    """
    if row is None:
        return None
    return {
        "id": row[0],
        "memory": row[1],
        "importance": row[2],
        "memory_type": row[3],
        "source": row[4],
        "source_reference": row[5],
        "confidence": row[6],
        "evidence": row[7],
        "is_active": bool(row[8]),
        "valid_from": row[9],
        "valid_until": row[10],
        "created_at": row[11],
        "updated_at": row[12],
        "supersedes_id": row[13],
        "user_id": row[14],
    }


_SELECT_COLUMNS = """
    id, memory, importance, memory_type, source, source_reference,
    confidence, evidence, is_active, valid_from, valid_until,
    created_at, updated_at, supersedes_id, user_id
"""


# -----------------------------
# Add Memory
# -----------------------------
def add_memory(
    memory,
    importance=5,
    memory_type="other",
    source="conversation",
    source_reference=None,
    confidence=0.7,
    evidence=None,
    user_id=None,
):
    """
    Backward compatible: existing callers using add_memory(text, importance)
    keep working unchanged and get sensible metadata defaults, with
    user_id defaulting to None (unowned/legacy, matching pre-auth
    behavior exactly when auth isn't in use).
    """

    if memory_exists(memory, user_id=user_id):
        print("Memory already exists:", memory)
        return

    if memory_type not in VALID_MEMORY_TYPES:
        memory_type = "other"

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO memories(
            memory, importance, memory_type, source, source_reference,
            confidence, evidence, is_active, valid_from, created_at, updated_at,
            user_id
        )
        VALUES(?, ?, ?, ?, ?, ?, ?, 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, ?)
        """,
        (memory, importance, memory_type, source, source_reference, confidence, evidence, user_id),
    )

    new_id = cursor.lastrowid

    cursor.execute(
        """
        INSERT INTO memory_history(memory_id, old_memory, new_memory, action)
        VALUES(?, NULL, ?, 'created')
        """,
        (new_id, memory),
    )

    conn.commit()
    conn.close()

    rebuild_memory_index_from_db()


# -----------------------------
# Get All Memories (backward compatible: still returns
# (id, memory, importance) tuples for existing callers like
# search_memory/prompt_builder, which only unpack 3 fields).
#
# user_id=None (the default) preserves EXACT original behavior:
# every active memory, unfiltered. This matters for any deployment
# not using auth at all. When user_id is given, results are scoped
# to that user only - memories created before auth was introduced
# (user_id IS NULL) are legacy/unowned and intentionally excluded
# from a specific account's results, mirroring the same convention
# already used for conversations.
# -----------------------------
def get_memories(include_inactive=False, user_id=None):
    conn = get_connection()
    cursor = conn.cursor()

    clauses = [] if include_inactive else ["is_active = 1"]
    params = []

    if user_id is not None:
        clauses.append("user_id = ?")
        params.append(user_id)
    else:
        # No specific user in context: only unowned/legacy memories,
        # never another account's owned data. In a true single-user
        # deployment every row has user_id IS NULL anyway, so this is
        # identical to "everything" there - it only changes behavior
        # (correctly) once some memories actually have an owner.
        clauses.append("user_id IS NULL")

    where_clause = f"WHERE {' AND '.join(clauses)}" if clauses else ""

    cursor.execute(
        f"""
        SELECT id, memory, importance
        FROM memories
        {where_clause}
        ORDER BY importance DESC
        """,
        params,
    )

    memories = cursor.fetchall()

    conn.close()

    return memories


def rebuild_memory_index_from_db():
    """
    Rebuilds the semantic memory search index across ALL memories
    (every user + legacy/unowned), each tagged with its owning
    user_id, so search_memory() can filter results per-user at query
    time. Kept as its own function so every mutation path rebuilds
    the same, fully-tagged index rather than the narrower, possibly
    single-user-filtered result of get_memories().
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, memory, importance, user_id FROM memories WHERE is_active = 1")
    rows = cursor.fetchall()
    conn.close()
    build_memory_index(rows)


# -----------------------------
# Get all memories with full metadata (for Memory Center UI)
# -----------------------------
def get_memories_detailed(memory_type=None, include_inactive=False, user_id=None):
    conn = get_connection()
    cursor = conn.cursor()

    clauses = []
    params = []

    if not include_inactive:
        clauses.append("is_active = 1")

    if memory_type:
        clauses.append("memory_type = ?")
        params.append(memory_type)

    if user_id is not None:
        clauses.append("user_id = ?")
        params.append(user_id)
    else:
        clauses.append("user_id IS NULL")

    where_clause = f"WHERE {' AND '.join(clauses)}" if clauses else ""

    cursor.execute(
        f"""
        SELECT {_SELECT_COLUMNS}
        FROM memories
        {where_clause}
        ORDER BY importance DESC, updated_at DESC
        """,
        params,
    )

    rows = cursor.fetchall()
    conn.close()

    return [_row_to_dict(row) for row in rows]


def get_memory_detail(memory_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        f"SELECT {_SELECT_COLUMNS} FROM memories WHERE id = ?",
        (memory_id,),
    )

    row = cursor.fetchone()
    conn.close()

    return _row_to_dict(row)


def get_memory_history(memory_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT id, memory_id, old_memory, new_memory, action, changed_at
        FROM memory_history
        WHERE memory_id = ?
        ORDER BY changed_at ASC
        """,
        (memory_id,),
    )

    rows = cursor.fetchall()
    conn.close()

    return [
        {
            "id": r[0],
            "memory_id": r[1],
            "old_memory": r[2],
            "new_memory": r[3],
            "action": r[4],
            "changed_at": r[5],
        }
        for r in rows
    ]


# -----------------------------
# Delete Memory (soft delete by default so history/evidence
# trails survive; hard delete kept available for the old
# API contract / privacy "forget this" requests)
# -----------------------------
def delete_memory(memory_id, hard_delete=True):
    conn = get_connection()
    cursor = conn.cursor()

    if hard_delete:
        # memory_history rows reference this memory_id via a foreign
        # key (added in the same migration that introduced history
        # tracking), so a hard delete must clear those first or it
        # fails with a foreign key violation. Also clear any row that
        # points to this memory as its supersedes_id predecessor, so
        # no memory is left referencing a deleted id.
        cursor.execute("DELETE FROM memory_history WHERE memory_id=?", (memory_id,))
        cursor.execute(
            "UPDATE memories SET supersedes_id = NULL WHERE supersedes_id = ?",
            (memory_id,),
        )
        cursor.execute("DELETE FROM memories WHERE id=?", (memory_id,))
    else:
        cursor.execute(
            "UPDATE memories SET is_active = 0, updated_at = CURRENT_TIMESTAMP WHERE id=?",
            (memory_id,),
        )

    conn.commit()
    conn.close()
    rebuild_memory_index_from_db()


def deactivate_memory(memory_id):
    delete_memory(memory_id, hard_delete=False)


def reactivate_memory(memory_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE memories SET is_active = 1, updated_at = CURRENT_TIMESTAMP WHERE id=?",
        (memory_id,),
    )
    conn.commit()
    conn.close()
    rebuild_memory_index_from_db()


# -----------------------------
# Supersede Memory (Temporal Memory / Feature 4)
#
# Used when a new fact CONTRADICTS an existing one for the same
# subject (e.g. CGPA 8.8 -> 8.97). Instead of overwriting the old
# row in place, we:
#   1. close out the old row: is_active=0, valid_until=now
#   2. insert a brand-new row for the new value, linked via
#      supersedes_id, with its own confidence/evidence/source
#
# This preserves a real timeline: "what was true when" can be
# reconstructed by walking supersedes_id, instead of only having a
# single mutated row with no record of what it used to say.
# -----------------------------
def supersede_memory(
    old_memory_id,
    new_memory,
    importance=5,
    memory_type=None,
    source="conversation",
    source_reference=None,
    confidence=0.7,
    evidence=None,
):
    old = get_memory_detail(old_memory_id)

    if old is None:
        # Nothing to supersede; fall back to a plain add.
        add_memory(
            new_memory, importance, memory_type=memory_type or "other",
            source=source, source_reference=source_reference,
            confidence=confidence, evidence=evidence,
        )
        return None

    if memory_type is None:
        memory_type = old["memory_type"]

    # Ownership never changes across a supersession - the new value
    # inherits whoever owned the old one.
    user_id = old["user_id"]

    conn = get_connection()
    cursor = conn.cursor()

    # Close out the old row
    cursor.execute(
        """
        UPDATE memories
        SET is_active = 0, valid_until = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """,
        (old_memory_id,),
    )

    # Insert the new, current row
    cursor.execute(
        """
        INSERT INTO memories(
            memory, importance, memory_type, source, source_reference,
            confidence, evidence, is_active, valid_from, created_at, updated_at,
            supersedes_id, user_id
        )
        VALUES(?, ?, ?, ?, ?, ?, ?, 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, ?, ?)
        """,
        (new_memory, importance, memory_type, source, source_reference,
         confidence, evidence, old_memory_id, user_id),
    )

    new_id = cursor.lastrowid

    cursor.execute(
        """
        INSERT INTO memory_history(memory_id, old_memory, new_memory, action)
        VALUES(?, ?, ?, 'contradiction_resolved')
        """,
        (new_id, old["memory"], new_memory),
    )

    conn.commit()
    conn.close()

    rebuild_memory_index_from_db()

    return new_id


def get_memory_chain(memory_id):
    """
    Walks the supersedes_id links for a memory's subject, returning
    the full timeline oldest -> newest, including inactive
    (superseded) entries. Accepts either the current or a historical
    memory_id in the chain.
    """
    detail = get_memory_detail(memory_id)
    if detail is None:
        return []

    # Walk forward to find the current (most recent) entry first.
    conn = get_connection()
    cursor = conn.cursor()

    current = detail
    while True:
        cursor.execute(
            f"SELECT {_SELECT_COLUMNS} FROM memories WHERE supersedes_id = ?",
            (current["id"],),
        )
        row = cursor.fetchone()
        if row is None:
            break
        current = _row_to_dict(row)

    # Now walk backward from the current entry to build the full chain.
    chain = [current]
    node = current
    while node.get("supersedes_id"):
        cursor.execute(
            f"SELECT {_SELECT_COLUMNS} FROM memories WHERE id = ?",
            (node["supersedes_id"],),
        )
        row = cursor.fetchone()
        if row is None:
            break
        node = _row_to_dict(row)
        chain.append(node)

    conn.close()

    chain.reverse()  # oldest first
    return chain


# -----------------------------
# Memory Context
# -----------------------------
def get_memory_context():
    memories = get_memories()

    if not memories:
        return ""

    memory_text = "Long-term memories:\n"

    for _, memory, importance in memories:
        memory_text += f"- {memory}\n"

    return memory_text


# -----------------------------
# Check if memory already exists
# -----------------------------
def memory_exists(memory, user_id=None):
    conn = get_connection()
    cursor = conn.cursor()

    if user_id is not None:
        cursor.execute(
            """
            SELECT id
            FROM memories
            WHERE LOWER(memory) = LOWER(?) AND user_id = ?
            """,
            (memory, user_id),
        )
    else:
        cursor.execute(
            """
            SELECT id
            FROM memories
            WHERE LOWER(memory) = LOWER(?) AND user_id IS NULL
            """,
            (memory,),
        )

    result = cursor.fetchone()

    conn.close()

    return result is not None


# -----------------------------
# Remove Duplicate Memories
# -----------------------------
def remove_duplicate_memories():
    conn = get_connection()
    cursor = conn.cursor()

    # Group by (text, owner) - not text alone - so two different
    # users independently stating the same fact are never treated as
    # duplicates of each other and one doesn't get deleted based on
    # someone else's memory.
    cursor.execute("""
        DELETE FROM memories
        WHERE id NOT IN (
            SELECT MIN(id)
            FROM memories
            GROUP BY LOWER(memory), COALESCE(user_id, -1)
        )
    """)

    conn.commit()
    conn.close()

    rebuild_memory_index_from_db()

    print("Duplicate memories removed.")


# -----------------------------
# Update Memory
# -----------------------------
def update_memory(memory_id, memory, importance, confidence=None, evidence=None, action="updated"):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT memory FROM memories WHERE id = ?", (memory_id,))
    row = cursor.fetchone()
    old_memory = row[0] if row else None

    if confidence is not None:
        cursor.execute(
            """
            UPDATE memories
            SET memory = ?, importance = ?, confidence = ?, evidence = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (memory, importance, confidence, evidence, memory_id),
        )
    else:
        cursor.execute(
            """
            UPDATE memories
            SET memory = ?, importance = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (memory, importance, memory_id),
        )

    cursor.execute(
        """
        INSERT INTO memory_history(memory_id, old_memory, new_memory, action)
        VALUES(?, ?, ?, ?)
        """,
        (memory_id, old_memory, memory, action),
    )

    conn.commit()
    conn.close()

    rebuild_memory_index_from_db()


def get_memory_by_text(memory_text, user_id=None):
    conn = get_connection()
    cursor = conn.cursor()

    if user_id is not None:
        cursor.execute(
            """
            SELECT id, memory, importance
            FROM memories
            WHERE memory=? AND user_id=?
            """,
            (memory_text, user_id),
        )
    else:
        cursor.execute(
            """
            SELECT id, memory, importance
            FROM memories
            WHERE memory=? AND user_id IS NULL
            """,
            (memory_text,),
        )

    result = cursor.fetchone()

    conn.close()

    return result


def update_memory_text(old_memory, new_memory):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE memories
        SET memory=?, updated_at = CURRENT_TIMESTAMP
        WHERE memory=?
        """,
        (
            new_memory,
            old_memory,
        ),
    )

    conn.commit()
    conn.close()

    rebuild_memory_index_from_db()


def get_contradictions(limit=50, user_id=None):
    """
    Every time the AI memory manager resolved a contradiction (old
    fact replaced by a new one), it's tagged in memory_history as
    'contradiction_resolved'. Single source of truth for this query -
    used by both the /memory/contradictions endpoint and the
    insights engine, so they can never disagree.
    """
    conn = get_connection()
    cursor = conn.cursor()

    if user_id is not None:
        cursor.execute(
            """
            SELECT h.id, h.memory_id, h.old_memory, h.new_memory, h.changed_at,
                   m.memory_type, m.confidence, m.evidence
            FROM memory_history h
            LEFT JOIN memories m ON m.id = h.memory_id
            WHERE h.action = 'contradiction_resolved' AND m.user_id = ?
            ORDER BY h.changed_at DESC
            LIMIT ?
            """,
            (user_id, limit),
        )
    else:
        cursor.execute(
            """
            SELECT h.id, h.memory_id, h.old_memory, h.new_memory, h.changed_at,
                   m.memory_type, m.confidence, m.evidence
            FROM memory_history h
            LEFT JOIN memories m ON m.id = h.memory_id
            WHERE h.action = 'contradiction_resolved' AND m.user_id IS NULL
            ORDER BY h.changed_at DESC
            LIMIT ?
            """,
            (limit,),
        )
    rows = cursor.fetchall()
    conn.close()

    return [
        {
            "history_id": r[0],
            "memory_id": r[1],
            "previous_value": r[2],
            "current_value": r[3],
            "changed_at": r[4],
            "memory_type": r[5],
            "confidence": r[6],
            "evidence": r[7],
        }
        for r in rows
    ]
