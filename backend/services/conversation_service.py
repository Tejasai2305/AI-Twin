from backend.database.database import get_connection


def get_history(conversation_id: int) -> str:
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT role, content
        FROM messages
        WHERE conversation_id = ?
        ORDER BY id
        """,
        (conversation_id,)
    )

    rows = cursor.fetchall()

    history = ""

    for role, content in rows:
        history += f"{role}: {content}\n"

    conn.close()

    return history


def save_message(conversation_id: int, role: str, content: str):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO messages (conversation_id, role, content)
        VALUES (?, ?, ?)
        """,
        (
            conversation_id,
            role,
            content
        )
    )

    conn.commit()
    conn.close()
def get_conversation_messages(conversation_id: int):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT id, role, content
        FROM messages
        WHERE conversation_id = ?
        ORDER BY id
        """,
        (conversation_id,)
    )

    messages = cursor.fetchall()

    conn.close()

    return messages