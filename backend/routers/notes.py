from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from backend.models.note import Note, NoteResponse
from backend.models.question import Question

from backend.services.title_generator import generate_title
from backend.services.title_service import update_conversation_title
from backend.services.conversation_service import (
    get_conversation_messages,
    save_message,
)

from backend.embeddings.vector_store import build_index

from backend.ai.gemini_service import ask_gemini_stream

from backend.services.agent_pipeline import process_chat
from backend.services import note_service

from backend.database.database import get_connection


router = APIRouter()


# ============================================================
# REQUEST MODELS
# ============================================================


class RegenerateRequest(BaseModel):
    conversation_id: int
    assistant_message_id: int

class EditMessageRequest(BaseModel):
    conversation_id: int
    user_message_id: int
    question: str
# ============================================================
# NOTES APIs
# ============================================================


@router.get("/notes")
def get_notes():
    return {
        "notes": note_service.get_notes()
    }


@router.post("/note", response_model=NoteResponse)
def create_note(note: Note):

    note_service.add_note(note)

    build_index(
        note_service.get_notes()
    )

    return {
        "title": note.title,
        "content": note.content,
        "status": "Saved Successfully"
    }


@router.put("/note/{id}", response_model=NoteResponse)
def update_note(
    id: int,
    updated_note: Note
):

    note_service.update_note(
        id,
        updated_note
    )

    build_index(
        note_service.get_notes()
    )

    return {
        "title": updated_note.title,
        "content": updated_note.content,
        "status": "Updated Successfully"
    }


@router.delete("/note/{id}")
def delete_note(id: int):

    note_service.delete_note(id)

    build_index(
        note_service.get_notes()
    )

    return {
        "message": f"Note {id} deleted successfully"
    }


# ============================================================
# HELPERS
# ============================================================


def attach_pending_files_to_message(
    conversation_id: int,
    message_id: int
):
    """
    Attach files uploaded for the conversation
    that have not yet been associated with a message.
    """

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE attachments
        SET message_id = ?
        WHERE conversation_id = ?
        AND message_id IS NULL
        """,
        (
            message_id,
            conversation_id,
        )
    )

    conn.commit()
    conn.close()


def get_message_for_regeneration(
    conversation_id: int,
    assistant_message_id: int,
):
    """
    Find the existing assistant message and the
    user message immediately preceding it.
    """

    conn = get_connection()
    cursor = conn.cursor()

    # --------------------------------------------------------
    # Verify assistant message
    # --------------------------------------------------------

    cursor.execute(
        """
        SELECT id, role, content
        FROM messages
        WHERE id = ?
        AND conversation_id = ?
        """,
        (
            assistant_message_id,
            conversation_id,
        )
    )

    assistant_row = cursor.fetchone()

    if not assistant_row:

        conn.close()

        raise HTTPException(
            status_code=404,
            detail="Assistant message not found."
        )

    if assistant_row[1] != "assistant":

        conn.close()

        raise HTTPException(
            status_code=400,
            detail="The selected message is not an assistant message."
        )

    # --------------------------------------------------------
    # Find preceding user message
    # --------------------------------------------------------

    cursor.execute(
        """
        SELECT id, content
        FROM messages
        WHERE conversation_id = ?
        AND role = 'user'
        AND id < ?
        ORDER BY id DESC
        LIMIT 1
        """,
        (
            conversation_id,
            assistant_message_id,
        )
    )

    user_row = cursor.fetchone()

    conn.close()

    if not user_row:

        raise HTTPException(
            status_code=400,
            detail="No user question found for this response."
        )

    return {
        "assistant_message_id": assistant_row[0],
        "assistant_content": assistant_row[2],
        "user_message_id": user_row[0],
        "question": user_row[1],
    }


def update_existing_assistant_message(
    message_id: int,
    content: str,
):
    """
    Replace the content of an existing assistant message.
    """

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE messages
        SET content = ?
        WHERE id = ?
        AND role = 'assistant'
        """,
        (
            content,
            message_id,
        )
    )

    conn.commit()

    updated = cursor.rowcount

    conn.close()

    if updated == 0:

        raise HTTPException(
            status_code=404,
            detail="Assistant message could not be updated."
        )

def get_message_for_edit(
    conversation_id: int,
    user_message_id: int,
):
    """
    Find the selected user message and the assistant
    response immediately following it.
    """

    conn = get_connection()
    cursor = conn.cursor()

    # --------------------------------------------------------
    # Verify user message
    # --------------------------------------------------------

    cursor.execute(
        """
        SELECT id, role, content
        FROM messages
        WHERE id = ?
        AND conversation_id = ?
        """,
        (
            user_message_id,
            conversation_id,
        )
    )

    user_row = cursor.fetchone()

    if not user_row:
        conn.close()

        raise HTTPException(
            status_code=404,
            detail="User message not found."
        )

    if user_row[1] != "user":
        conn.close()

        raise HTTPException(
            status_code=400,
            detail="The selected message is not a user message."
        )

    # --------------------------------------------------------
    # Find assistant response immediately after it
    # --------------------------------------------------------

    cursor.execute(
        """
        SELECT id, role, content
        FROM messages
        WHERE conversation_id = ?
        AND role = 'assistant'
        AND id > ?
        ORDER BY id ASC
        LIMIT 1
        """,
        (
            conversation_id,
            user_message_id,
        )
    )

    assistant_row = cursor.fetchone()

    conn.close()

    if not assistant_row:
        raise HTTPException(
            status_code=400,
            detail="No assistant response found for this message."
        )

    return {
        "user_message_id": user_row[0],
        "original_question": user_row[2],
        "assistant_message_id": assistant_row[0],
    }


def update_existing_user_message(
    message_id: int,
    content: str,
):
    """
    Replace the content of an existing user message.
    """

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE messages
        SET content = ?
        WHERE id = ?
        AND role = 'user'
        """,
        (
            content,
            message_id,
        )
    )

    conn.commit()

    updated = cursor.rowcount

    conn.close()

    if updated == 0:
        raise HTTPException(
            status_code=404,
            detail="User message could not be updated."
        )
# ============================================================
# NORMAL AI CHAT
# ============================================================


@router.post("/ask")
def ask_question(question: Question):

    result = process_chat(
        question
    )

    # --------------------------------------------------------
    # Tool-handled request
    # --------------------------------------------------------

    if result["handled"]:

        tool_result = result["response"]

        user_message_id = save_message(
            question.conversation_id,
            "user",
            question.question,
        )

        attach_pending_files_to_message(
            question.conversation_id,
            user_message_id,
        )

        assistant_text = str(
            tool_result["result"]["result"]
        )

        save_message(
            question.conversation_id,
            "assistant",
            assistant_text,
        )

        return assistant_text

    # --------------------------------------------------------
    # Normal AI response
    # --------------------------------------------------------

    state = result["state"]

    answer = state.answer

    user_message_id = save_message(
        question.conversation_id,
        "user",
        question.question,
    )

    attach_pending_files_to_message(
        question.conversation_id,
        user_message_id,
    )

    save_message(
        question.conversation_id,
        "assistant",
        answer,
    )

    return {
        "question": question.question,
        "answer": answer,
        "mode": state.mode,
        "sources": [
            {
                "file": result["state"].pdf_results[i]["filename"]
                if isinstance(
                    result["state"].pdf_results[i],
                    dict
                )
                and "filename"
                in result["state"].pdf_results[i]
                else None
            }
            for i in range(
                len(result["state"].pdf_results)
            )
        ]
    }


# ============================================================
# STREAMING AI CHAT
# ============================================================


@router.post("/ask-stream")
def ask_question_stream(
    question: Question
):

    # --------------------------------------------------------
    # Run pipeline without calling Gemini
    # --------------------------------------------------------

    result = process_chat(
        question,
        generate_answer=False
    )

    # --------------------------------------------------------
    # Tool-handled request
    # --------------------------------------------------------

    if result["handled"]:

        tool_result = result["response"]

        assistant_text = str(
            tool_result["result"]["result"]
        )

        user_message_id = save_message(
            question.conversation_id,
            "user",
            question.question,
        )

        attach_pending_files_to_message(
            question.conversation_id,
            user_message_id,
        )

        save_message(
            question.conversation_id,
            "assistant",
            assistant_text,
        )

        def generate_tool():

            yield assistant_text

        return StreamingResponse(
            generate_tool(),
            media_type="text/plain",
        )

    # --------------------------------------------------------
    # Pipeline state
    # --------------------------------------------------------

    state = result["state"]

    # --------------------------------------------------------
    # Generate title for first message
    # --------------------------------------------------------

    messages = get_conversation_messages(
        question.conversation_id
    )

    if len(messages) == 0:

        title = generate_title(
            question.question
        )

        print("=" * 60)
        print("QUESTION:")
        print(repr(question.question))
        print("TITLE:")
        print(repr(title))
        print("=" * 60)

        update_conversation_title(
            question.conversation_id,
            title,
        )

    # --------------------------------------------------------
    # Save user message BEFORE Gemini streaming
    # --------------------------------------------------------

    user_message_id = save_message(
        question.conversation_id,
        "user",
        question.question,
    )

    # --------------------------------------------------------
    # Attach uploaded PDFs
    # --------------------------------------------------------

    attach_pending_files_to_message(
        question.conversation_id,
        user_message_id,
    )

    # --------------------------------------------------------
    # Final prompt
    # --------------------------------------------------------

    prompt = state.prompt

    # --------------------------------------------------------
    # Stream Gemini
    # --------------------------------------------------------

    def generate():

        full_answer = ""

        try:

            for chunk in ask_gemini_stream(prompt):

                full_answer += chunk

                yield chunk

            save_message(
                question.conversation_id,
                "assistant",
                full_answer,
            )

        except Exception as e:

            print(
                "STREAM ERROR:",
                e
            )

            raise

    return StreamingResponse(
        generate(),
        media_type="text/plain",
    )


# ============================================================
# REGENERATE AI RESPONSE
# ============================================================


@router.post("/regenerate-stream")
def regenerate_response(
    request: RegenerateRequest
):

    # --------------------------------------------------------
    # Find existing messages
    # --------------------------------------------------------

    message_data = get_message_for_regeneration(
        request.conversation_id,
        request.assistant_message_id,
    )

    question_text = message_data["question"]

    print("=" * 60)
    print("REGENERATING RESPONSE")
    print(
        "Conversation ID:",
        request.conversation_id
    )
    print(
        "Assistant Message ID:",
        request.assistant_message_id
    )
    print(
        "Original Question:",
        question_text
    )
    print("=" * 60)

    # --------------------------------------------------------
    # Recreate Question object
    # --------------------------------------------------------

    question = Question(
        conversation_id=request.conversation_id,
        question=question_text,
    )

    # --------------------------------------------------------
    # Run pipeline without generating answer
    # --------------------------------------------------------

    result = process_chat(
        question,
        generate_answer=False,
    )

    # --------------------------------------------------------
    # Tool-handled request
    # --------------------------------------------------------

    if result["handled"]:

        tool_result = result["response"]

        assistant_text = str(
            tool_result["result"]["result"]
        )

        def generate_tool():

            yield assistant_text

            update_existing_assistant_message(
                request.assistant_message_id,
                assistant_text,
            )

        return StreamingResponse(
            generate_tool(),
            media_type="text/plain",
        )

    # --------------------------------------------------------
    # Normal AI regeneration
    # --------------------------------------------------------

    state = result["state"]

    prompt = state.prompt

    def generate():

        full_answer = ""

        try:

            for chunk in ask_gemini_stream(prompt):

                full_answer += chunk

                yield chunk

            # ------------------------------------------------
            # Update EXISTING assistant message
            # ------------------------------------------------

            update_existing_assistant_message(
                request.assistant_message_id,
                full_answer,
            )

            print(
                "Assistant response regenerated successfully."
            )

        except Exception as e:

            print(
                "REGENERATE STREAM ERROR:",
                e
            )

            raise

    return StreamingResponse(
        generate(),
        media_type="text/plain",
    )
# ============================================================
# EDIT USER MESSAGE AND REGENERATE RESPONSE
# ============================================================


@router.post("/edit-message-stream")
def edit_message_stream(
    request: EditMessageRequest
):

    # --------------------------------------------------------
    # Validate question
    # --------------------------------------------------------

    question_text = request.question.strip()

    if not question_text:
        raise HTTPException(
            status_code=400,
            detail="Question cannot be empty."
        )

    # --------------------------------------------------------
    # Find user + assistant messages
    # --------------------------------------------------------

    message_data = get_message_for_edit(
        request.conversation_id,
        request.user_message_id,
    )

    assistant_message_id = (
        message_data["assistant_message_id"]
    )

    print("=" * 60)
    print("EDIT & RESEND")
    print(
        "Conversation ID:",
        request.conversation_id
    )
    print(
        "User Message ID:",
        request.user_message_id
    )
    print(
        "Assistant Message ID:",
        assistant_message_id
    )
    print(
        "Original Question:",
        message_data["original_question"]
    )
    print(
        "New Question:",
        question_text
    )
    print("=" * 60)

    # --------------------------------------------------------
    # Update existing user message
    # --------------------------------------------------------

    update_existing_user_message(
        request.user_message_id,
        question_text,
    )

    # --------------------------------------------------------
    # Recreate Question object
    # --------------------------------------------------------

    question = Question(
        conversation_id=request.conversation_id,
        question=question_text,
    )

    # --------------------------------------------------------
    # Run pipeline
    # --------------------------------------------------------

    result = process_chat(
        question,
        generate_answer=False,
    )

    # --------------------------------------------------------
    # Tool-handled request
    # --------------------------------------------------------

    if result["handled"]:

        tool_result = result["response"]

        assistant_text = str(
            tool_result["result"]["result"]
        )

        def generate_tool():

            yield assistant_text

            update_existing_assistant_message(
                assistant_message_id,
                assistant_text,
            )

        return StreamingResponse(
            generate_tool(),
            media_type="text/plain",
        )

    # --------------------------------------------------------
    # Normal AI response
    # --------------------------------------------------------

    state = result["state"]

    prompt = state.prompt

    def generate():

        full_answer = ""

        try:

            for chunk in ask_gemini_stream(prompt):

                full_answer += chunk

                yield chunk

            # ------------------------------------------------
            # Update existing assistant message
            # ------------------------------------------------

            update_existing_assistant_message(
                assistant_message_id,
                full_answer,
            )

            print(
                "Edited response generated successfully."
            )

        except Exception as e:

            print(
                "EDIT STREAM ERROR:",
                e
            )

            raise

    return StreamingResponse(
        generate(),
        media_type="text/plain",
    )
