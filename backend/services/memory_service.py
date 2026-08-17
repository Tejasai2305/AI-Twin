import sqlite3
import os
from pathlib import Path

from backend.embeddings.memory_vector_store import build_memory_index

BASE_DIR = Path(__file__).resolve().parent.parent.parent

DATA_DIR = Path(
    os.getenv("AI_TWIN_DATA_DIR", str(BASE_DIR))
)

DATA_DIR.mkdir(parents=True, exist_ok=True)

DB_NAME = DATA_DIR / "notes.db"


def get_connection():
    return sqlite3.connect(DB_NAME)
# -----------------------------
# Add Memory
# -----------------------------
def add_memory(memory, importance=5):

    if memory_exists(memory):
        print("Memory already exists:", memory)
        return

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO memories(memory, importance)
        VALUES(?, ?)
        """,
        (memory, importance),
    )

    conn.commit()
    conn.close()

    build_memory_index(get_memories())
# -----------------------------
# Get All Memories
# -----------------------------
def get_memories():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, memory, importance
        FROM memories
        ORDER BY importance DESC
    """)

    memories = cursor.fetchall()

    conn.close()

    return memories


# -----------------------------
# Delete Memory
# -----------------------------
def delete_memory(memory_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        DELETE FROM memories
        WHERE id=?
        """,
        (memory_id,),
    )

    conn.commit()
    conn.close()
    build_memory_index(get_memories())

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
def memory_exists(memory):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT id
        FROM memories
        WHERE LOWER(memory) = LOWER(?)
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

    cursor.execute("""
        DELETE FROM memories
        WHERE id NOT IN (
            SELECT MIN(id)
            FROM memories
            GROUP BY LOWER(memory)
        )
    """)

    conn.commit()
    conn.close()

    build_memory_index(get_memories())

    print("Duplicate memories removed.")
    

# -----------------------------
# Update Memory
# -----------------------------
def update_memory(memory_id, memory, importance):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE memories
        SET memory = ?, importance = ?
        WHERE id = ?
        """,
        (memory, importance, memory_id),
    )

    conn.commit()
    conn.close()

    build_memory_index(get_memories())
def get_memory_by_text(memory_text):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT id, memory, importance
        FROM memories
        WHERE memory=?
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
        SET memory=?
        WHERE memory=?
        """,
        (
            new_memory,
            old_memory,
        ),
    )

    conn.commit()
    conn.close()

    build_memory_index(get_memories())