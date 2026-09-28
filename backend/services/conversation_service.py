from backend.database.database import get_connection


def get_conversation_owner(conversation_id: int):
    """
    Returns the user_id that owns this conversation, or None if the
    conversation is unowned (created before auth was introduced, or
    auth isn't in use at all). Used to scope memory reads/writes made
    during chat to the conversation's owner without threading an auth
    dependency through every streaming chat endpoint.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM conversations WHERE id = ?", (conversation_id,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else None


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


def save_message(
    conversation_id: int,
    role: str,
    content: str
):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO messages (
            conversation_id,
            role,
            content
        )
        VALUES (?, ?, ?)
        """,
        (
            conversation_id,
            role,
            content
        )
    )

    message_id = cursor.lastrowid

    conn.commit()
    conn.close()

    return message_id


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