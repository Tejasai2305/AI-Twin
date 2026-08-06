from fastapi import APIRouter
from backend.database.database import get_connection
from backend.models.conversation import Conversation, ConversationResponse

router = APIRouter()


@router.post("/conversation", response_model=ConversationResponse)
def create_conversation(conversation: Conversation):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO conversations (title) VALUES (?)",
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
@router.get("/conversations")
def get_conversations():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, title, created_at
        FROM conversations
        ORDER BY created_at DESC
    """)

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
@router.get("/conversation/{conversation_id}")
def get_conversation(conversation_id: int):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT role, content, created_at
        FROM messages
        WHERE conversation_id = ?
        ORDER BY created_at ASC
        """,
        (conversation_id,)
    )

    messages = cursor.fetchall()

    conn.close()

    return [
        {
            "role": row[0],
            "content": row[1],
            "created_at": row[2]
        }
        for row in messages
    ]