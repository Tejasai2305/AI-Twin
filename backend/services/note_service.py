from backend.database.database import get_connection, create_table
from backend.embeddings.vector_store import (
    build_index,
    search_documents
)
create_table()


def get_notes():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id, title, content FROM notes")

    rows = cursor.fetchall()

    conn.close()

    return [
        {
            "id": row[0],
            "title": row[1],
            "content": row[2]
        }
        for row in rows
    ]


def add_note(note):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO notes (title, content) VALUES (?, ?)",
        (note.title, note.content)
    )

    conn.commit()
    conn.close()
   


def update_note(id, updated_note):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE notes
        SET title = ?, content = ?
        WHERE id = ?
        """,
        (
            updated_note.title,
            updated_note.content,
            id
        )
    )

    conn.commit()
    conn.close()
  


def delete_note(id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM notes WHERE id = ?",
        (id,)
    )

    conn.commit()
    conn.close()
   
    
def search_notes(question):

    results = search_documents(question)

    return results