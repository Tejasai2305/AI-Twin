from fastapi import APIRouter, HTTPException, Depends

from backend.database.database import get_connection
from backend.models.conversation import (
    Conversation,
    ConversationResponse,
)
from backend.auth.dependencies import get_optional_user

router = APIRouter()


# ============================================================
# CREATE CONVERSATION
# ============================================================

@router.post(
    "/conversation",
    response_model=ConversationResponse
)
def create_conversation(conversation: Conversation, current_user=Depends(get_optional_user)):

    conn = get_connection()
    cursor = conn.cursor()

    user_id = current_user["id"] if current_user else None

    cursor.execute(
        """
        INSERT INTO conversations (title, user_id)
        VALUES (?, ?)
        """,
        (conversation.title, user_id)
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
def get_conversations(current_user=Depends(get_optional_user)):

    conn = get_connection()
    cursor = conn.cursor()

    if current_user:
        # Authenticated: only this user's own conversations. Rows
        # created before auth was introduced (user_id IS NULL) are
        # legacy/unowned and intentionally not shown to any specific
        # account, since they can't be attributed to one.
        cursor.execute(
            """
            SELECT
                id,
                title,
                created_at
            FROM conversations
            WHERE user_id = ?
            ORDER BY created_at DESC
            """,
            (current_user["id"],),
        )
    else:
        # No auth in use (single-user/desktop mode): unchanged,
        # original behavior.
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
def search_conversations(q: str = "", current_user=Depends(get_optional_user)):

    conn = get_connection()
    cursor = conn.cursor()

    query = q.strip()
    user_id = current_user["id"] if current_user else None

    # --------------------------------------------------------
    # Empty search
    # --------------------------------------------------------

    if not query:

        if user_id is not None:
            cursor.execute(
                """
                SELECT
                    id,
                    title,
                    created_at
                FROM conversations
                WHERE user_id = ?
                ORDER BY created_at DESC
                """,
                (user_id,),
            )
        else:
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

    if user_id is not None:
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
                c.user_id = ?
                AND (c.title LIKE ? OR m.content LIKE ?)

            ORDER BY
                c.created_at DESC,
                m.id DESC
            """,
            (
                user_id,
                pattern,
                pattern,
            )
        )
    else:
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
def get_conversation(conversation_id: int, current_user=Depends(get_optional_user)):

    conn = get_connection()
    cursor = conn.cursor()

    # --------------------------------------------------------
    # Check conversation exists AND belongs to the requester
    # --------------------------------------------------------

    cursor.execute(
        """
        SELECT
            id,
            title,
            created_at,
            user_id
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

    owner_id = conversation_row[3]
    requester_id = current_user["id"] if current_user else None

    if owner_id != requester_id:

        conn.close()

        # Same response as "doesn't exist" - never reveal that a
        # conversation exists but belongs to someone else.
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

def _get_conversation_owner_or_404(cursor, conversation_id):
    """Shared ownership lookup for rename/delete - raises 404 if the
    conversation doesn't exist. Returns the owner's user_id (or None
    for unowned/legacy conversations)."""
    cursor.execute(
        "SELECT user_id FROM conversations WHERE id = ?",
        (conversation_id,),
    )
    row = cursor.fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return row[0]


def _assert_conversation_owned(cursor, conversation_id, current_user):
    owner_id = _get_conversation_owner_or_404(cursor, conversation_id)
    requester_id = current_user["id"] if current_user else None
    if owner_id != requester_id:
        # Same response as "doesn't exist".
        raise HTTPException(status_code=404, detail="Conversation not found")


@router.put("/conversation/{conversation_id}")
def rename_conversation(
    conversation_id: int,
    conversation: Conversation,
    current_user=Depends(get_optional_user),
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
    # Check conversation exists and belongs to the requester
    # --------------------------------------------------------

    try:
        _assert_conversation_owned(cursor, conversation_id, current_user)
    except HTTPException:
        conn.close()
        raise

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
    conversation_id: int,
    current_user=Depends(get_optional_user),
):

    conn = get_connection()
    cursor = conn.cursor()

    # --------------------------------------------------------
    # Check conversation exists and belongs to the requester
    # --------------------------------------------------------

    try:
        _assert_conversation_owned(cursor, conversation_id, current_user)
    except HTTPException:
        conn.close()
        raise

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