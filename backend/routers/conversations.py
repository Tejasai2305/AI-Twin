from fastapi import APIRouter, HTTPException

from backend.database.database import get_connection
from backend.models.conversation import (
    Conversation,
    ConversationResponse,
)

router = APIRouter()


# ============================================================
# CREATE CONVERSATION
# ============================================================

@router.post(
    "/conversation",
    response_model=ConversationResponse
)
def create_conversation(conversation: Conversation):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO conversations (title)
        VALUES (?)
        """,
        (conversation.title,)
    )

    conn.commit()

    conversation_id = cursor.lastrowid

    conn.close()

    return ConversationResponse(
        id=conversation_id,
        title=conversation.title,
        status="Conversation created successfully"
    )


# ============================================================
# GET ALL CONVERSATIONS
# ============================================================

@router.get("/conversations")
def get_conversations():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            id,
            title,
            created_at
        FROM conversations
        ORDER BY created_at DESC
        """
    )

    conversations = cursor.fetchall()

    conn.close()

    return [
        {
            "id": row[0],
            "title": row[1],
            "created_at": row[2]
        }
        for row in conversations
    ]


# ============================================================
# SEARCH CONVERSATIONS
# ============================================================

@router.get("/conversations/search")
def search_conversations(q: str = ""):

    conn = get_connection()
    cursor = conn.cursor()

    query = q.strip()

    # --------------------------------------------------------
    # Empty search
    # --------------------------------------------------------

    if not query:

        cursor.execute(
            """
            SELECT
                id,
                title,
                created_at
            FROM conversations
            ORDER BY created_at DESC
            """
        )

        rows = cursor.fetchall()

        conn.close()

        return [
            {
                "id": row[0],
                "title": row[1],
                "created_at": row[2],
                "match": None,
            }
            for row in rows
        ]

    # --------------------------------------------------------
    # Search conversation titles AND message contents
    # --------------------------------------------------------

    pattern = f"%{query}%"

    cursor.execute(
        """
        SELECT
            c.id,
            c.title,
            c.created_at,
            m.content,
            m.id
        FROM conversations AS c

        LEFT JOIN messages AS m
            ON c.id = m.conversation_id

        WHERE
            c.title LIKE ?
            OR m.content LIKE ?

        ORDER BY
            c.created_at DESC,
            m.id DESC
        """,
        (
            pattern,
            pattern,
        )
    )

    rows = cursor.fetchall()

    conn.close()

    # --------------------------------------------------------
    # One result per conversation
    #
    # Because a conversation can contain multiple matching
    # messages, keep only the newest matching message.
    # --------------------------------------------------------

    results = []
    seen = set()

    for row in rows:

        conversation_id = row[0]
        title = row[1]
        created_at = row[2]
        message_content = row[3]

        if conversation_id in seen:
            continue

        seen.add(conversation_id)

        # If the title matched but the message didn't,
        # there may be no matching message content.
        match_text = message_content

        results.append(
            {
                "id": conversation_id,
                "title": title,
                "created_at": created_at,
                "match": match_text,
            }
        )

    return results


# ============================================================
# GET SINGLE CONVERSATION
# ============================================================

@router.get("/conversation/{conversation_id}")
def get_conversation(conversation_id: int):

    conn = get_connection()
    cursor = conn.cursor()

    # --------------------------------------------------------
    # Check conversation exists
    # --------------------------------------------------------

    cursor.execute(
        """
        SELECT
            id,
            title,
            created_at
        FROM conversations
        WHERE id = ?
        """,
        (conversation_id,)
    )

    conversation_row = cursor.fetchone()

    if conversation_row is None:

        conn.close()

        raise HTTPException(
            status_code=404,
            detail="Conversation not found"
        )

    # --------------------------------------------------------
    # Get messages
    # --------------------------------------------------------

    cursor.execute(
        """
        SELECT
            id,
            role,
            content,
            created_at
        FROM messages
        WHERE conversation_id = ?
        ORDER BY id ASC
        """,
        (conversation_id,)
    )

    message_rows = cursor.fetchall()

    # --------------------------------------------------------
    # Get attachments
    # --------------------------------------------------------

    cursor.execute(
        """
        SELECT
            id,
            message_id,
            filename,
            file_type,
            file_path,
            created_at
        FROM attachments
        WHERE conversation_id = ?
        ORDER BY id ASC
        """,
        (conversation_id,)
    )

    attachment_rows = cursor.fetchall()

    conn.close()

    # --------------------------------------------------------
    # Build attachment lookup
    # --------------------------------------------------------

    attachments_by_message = {}

    for row in attachment_rows:

        attachment_id = row[0]
        message_id = row[1]
        filename = row[2]
        file_type = row[3]
        file_path = row[4]
        created_at = row[5]

        attachment = {
            "id": attachment_id,
            "filename": filename,
            "name": filename,
            "file_type": file_type,
            "type": file_type,
            "file_path": file_path,
            "created_at": created_at,
        }

        if message_id is not None:

            if message_id not in attachments_by_message:
                attachments_by_message[message_id] = []

            attachments_by_message[message_id].append(
                attachment
            )

    # --------------------------------------------------------
    # Build messages
    # --------------------------------------------------------

    messages = []

    for row in message_rows:

        message_id = row[0]

        messages.append(
            {
                "id": message_id,
                "role": row[1],
                "content": row[2],
                "created_at": row[3],
                "attachments": attachments_by_message.get(
                    message_id,
                    []
                ),
            }
        )

    # --------------------------------------------------------
    # Return conversation
    # --------------------------------------------------------

    return {
        "id": conversation_row[0],
        "title": conversation_row[1],
        "created_at": conversation_row[2],
        "messages": messages,
    }


# ============================================================
# RENAME CONVERSATION
# ============================================================

@router.put("/conversation/{conversation_id}")
def rename_conversation(
    conversation_id: int,
    conversation: Conversation
):

    title = conversation.title.strip()

    if not title:

        raise HTTPException(
            status_code=400,
            detail="Conversation title cannot be empty"
        )

    conn = get_connection()
    cursor = conn.cursor()

    # --------------------------------------------------------
    # Check conversation exists
    # --------------------------------------------------------

    cursor.execute(
        """
        SELECT id
        FROM conversations
        WHERE id = ?
        """,
        (conversation_id,)
    )

    if cursor.fetchone() is None:

        conn.close()

        raise HTTPException(
            status_code=404,
            detail="Conversation not found"
        )

    # --------------------------------------------------------
    # Update title
    # --------------------------------------------------------

    cursor.execute(
        """
        UPDATE conversations
        SET title = ?
        WHERE id = ?
        """,
        (
            title,
            conversation_id,
        )
    )

    conn.commit()
    conn.close()

    return {
        "id": conversation_id,
        "title": title,
        "status": "Conversation renamed successfully"
    }


# ============================================================
# DELETE CONVERSATION
# ============================================================

@router.delete("/conversation/{conversation_id}")
def delete_conversation(
    conversation_id: int
):

    conn = get_connection()
    cursor = conn.cursor()

    # --------------------------------------------------------
    # Check conversation exists
    # --------------------------------------------------------

    cursor.execute(
        """
        SELECT id
        FROM conversations
        WHERE id = ?
        """,
        (conversation_id,)
    )

    if cursor.fetchone() is None:

        conn.close()

        raise HTTPException(
            status_code=404,
            detail="Conversation not found"
        )

    # --------------------------------------------------------
    # Get attachment file paths
    # --------------------------------------------------------

    cursor.execute(
        """
        SELECT file_path
        FROM attachments
        WHERE conversation_id = ?
        """,
        (conversation_id,)
    )

    attachment_paths = [
        row[0]
        for row in cursor.fetchall()
        if row[0]
    ]

    # --------------------------------------------------------
    # Delete attachments
    # --------------------------------------------------------

    cursor.execute(
        """
        DELETE FROM attachments
        WHERE conversation_id = ?
        """,
        (conversation_id,)
    )

    # --------------------------------------------------------
    # Delete messages
    # --------------------------------------------------------

    cursor.execute(
        """
        DELETE FROM messages
        WHERE conversation_id = ?
        """,
        (conversation_id,)
    )

    # --------------------------------------------------------
    # Delete conversation
    # --------------------------------------------------------

    cursor.execute(
        """
        DELETE FROM conversations
        WHERE id = ?
        """,
        (conversation_id,)
    )

    conn.commit()
    conn.close()

    # --------------------------------------------------------
    # Delete physical uploaded files
    # --------------------------------------------------------

    import os

    for file_path in attachment_paths:

        try:

            if os.path.exists(file_path):
                os.remove(file_path)

        except OSError as error:

            print(
                f"Could not delete file {file_path}: {error}"
            )

    return {
        "id": conversation_id,
        "status": "Conversation deleted successfully"
    }