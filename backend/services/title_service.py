from backend.database.database import get_connection


def update_conversation_title(conversation_id, title):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE conversations
        SET title=?
        WHERE id=?
        """,
        (title, conversation_id),
    )

    conn.commit()
    conn.close()