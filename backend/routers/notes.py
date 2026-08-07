from fastapi import APIRouter

from backend.models import question
from backend.models.note import Note, NoteResponse
from backend.models.question import Question
from backend.agent.controller import process_request
from backend.ai.gemini_service import ask_gemini
from backend.services.title_generator import generate_title
from backend.services.title_service import update_conversation_title
from backend.services.conversation_service import get_conversation_messages
from backend.embeddings.vector_store import build_index
from fastapi.responses import StreamingResponse
from backend.ai.gemini_service import ask_gemini_stream

from backend.services.agent_pipeline import process_chat
from backend.services import note_service
from backend.services.router_service import classify_question
from backend.services.retrieval_service import retrieve_context
from backend.services.prompt_builder import build_prompt
from backend.services.conversation_service import (
    get_history,
    save_message,
)

router = APIRouter()


# -----------------------------
# Notes APIs
# -----------------------------

@router.get("/notes")
def get_notes():
    return {
        "notes": note_service.get_notes()
    }


@router.post("/note", response_model=NoteResponse)
def create_note(note: Note):

    note_service.add_note(note)

    build_index(note_service.get_notes())

    return {
        "title": note.title,
        "content": note.content,
        "status": "Saved Successfully"
    }


@router.put("/note/{id}", response_model=NoteResponse)
def update_note(id: int, updated_note: Note):

    note_service.update_note(id, updated_note)

    build_index(note_service.get_notes())

    return {
        "title": updated_note.title,
        "content": updated_note.content,
        "status": "Updated Successfully"
    }


@router.delete("/note/{id}")
def delete_note(id: int):

    note_service.delete_note(id)

    build_index(note_service.get_notes())

    return {
        "message": f"Note {id} deleted successfully"
    }


# -----------------------------
# AI Chat
# -----------------------------

@router.post("/ask")
def ask_question(question: Question):
    result = process_chat(question)

    if result["handled"]:
        return result["response"]
    # -----------------------------
    # Agent Tool Check
    # -----------------------------
    tool_result = process_request(question.question)

    result = process_chat(question)

    if result["handled"]:

        tool_result = result["response"]

        tool_result = result["response"]

    return {
        "question": question.question,
        "answer": str(tool_result["result"]["result"]),
        "mode": "tool",
        "sources": [],
    }
    # -----------------------------
    # Decide which context to use
    # -----------------------------
    mode = classify_question(question.question)
    print(f"Mode: {mode}")

    # -----------------------------
    # Retrieve conversation history
    # -----------------------------
    history = ""
    if mode in ["conversation", "hybrid"]:
        history = get_history(question.conversation_id)

    # -----------------------------
    # Retrieve notes + PDF context
    # -----------------------------
    notes_text, pdf_text, pdf_results = retrieve_context(
        mode,
        question.question,
    )

    # -----------------------------
    # Build prompt
    # -----------------------------
    prompt = build_prompt(
        mode,
        history,
        notes_text,
        pdf_text,
        question.question,
    )

    # -----------------------------
    # Ask Gemini
    # -----------------------------
    state = result["state"]

    answer = state.answer

    # -----------------------------
    # Save conversation
    # -----------------------------
    save_message(
        question.conversation_id,
        "user",
        question.question,
    )

    save_message(
        question.conversation_id,
        "assistant",
        answer,
    )

    return {
        "question": question.question,
        "answer": answer,
        "mode": mode,
        "sources": [
            {
                "file": result["filename"],
                "chunk": result["chunk_id"],
            }
            for result in pdf_results
        ],
    }
@router.post("/ask-stream")
def ask_question_stream(question: Question):

    result = process_chat(question)

    if result["handled"]:

        tool_result = result["response"]

        def generate():
            yield str(tool_result["result"]["result"])

        return StreamingResponse(
            generate(),
            media_type="text/plain",
        )

    # -----------------------------
    # Decide which context to use
    # -----------------------------
    
    # -----------------------------
    # Decide which context to use
    # -----------------------------
    state = result["state"]

    mode = state.mode
    history = state.history

    # -----------------------------
    # Generate title for first message
    # -----------------------------
    messages = get_conversation_messages(question.conversation_id)

    if len(messages) == 0:
        title = generate_title(question.question)
        update_conversation_title(
            question.conversation_id,
            title,
        )

    # -----------------------------
    # Retrieve notes + PDF context
    # -----------------------------
    state = result["state"]

    notes_text = state.notes
    pdf_text = state.pdf
    pdf_results = state.pdf_results

    # -----------------------------
    # Build prompt
    # -----------------------------
    state = result["state"]

    prompt = state.prompt

    # -----------------------------
    # Stream Gemini response
    # -----------------------------
    def generate():
        full_answer = ""

        try:
            for chunk in ask_gemini_stream(prompt):
                full_answer += chunk
                yield chunk

            save_message(
                question.conversation_id,
                "user",
                question.question,
            )

            save_message(
                question.conversation_id,
                "assistant",
                full_answer,
            )

        except Exception as e:
            print("STREAM ERROR:", e)
            raise

    return StreamingResponse(
        generate(),
        media_type="text/plain",
    )