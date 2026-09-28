from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
import os
import uuid
from pathlib import Path

from backend.documents.pdf_service import extract_text_from_pdf
from backend.documents.chunking import split_text
from backend.documents.pdf_vector_store import build_pdf_index
from backend.database.database import get_connection
from backend.auth.dependencies import get_optional_user


router = APIRouter()


BASE_DIR = Path(__file__).resolve().parent.parent.parent

DATA_DIR = Path(
    os.getenv("AI_TWIN_DATA_DIR", str(BASE_DIR))
)

UPLOAD_FOLDER = DATA_DIR / "uploads"

UPLOAD_FOLDER.mkdir(
    parents=True,
    exist_ok=True
)

MAX_UPLOAD_BYTES = 20 * 1024 * 1024  # 20 MB


@router.post("/upload-pdf")
async def upload_pdf(
    file: UploadFile = File(...),
    conversation_id: int = Form(...),
    current_user=Depends(get_optional_user),
):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT id, user_id FROM conversations WHERE id = ?",
        (conversation_id,),
    )

    conversation = cursor.fetchone()
    conn.close()

    if conversation is None:
        raise HTTPException(
            status_code=404,
            detail="Conversation not found.",
        )

    # --------------------------------------------------------
    # Ownership check: without this, any user could upload a PDF
    # into another account's conversation_id, injecting arbitrary
    # document content into that user's retrieval context - the
    # same class of cross-user issue as the chat/conversation
    # hijacks fixed elsewhere. Same 404-either-way response so
    # existence of someone else's conversation is never confirmed.
    # --------------------------------------------------------

    owner_id = conversation[1]
    requester_id = current_user["id"] if current_user else None

    if owner_id != requester_id:
        raise HTTPException(
            status_code=404,
            detail="Conversation not found.",
        )

    # filename validation continues here...
    # --------------------------------------------------------
    # Validate uploaded filename
    # --------------------------------------------------------

    safe_filename = Path(file.filename or "").name

    if not safe_filename:
        raise HTTPException(
            status_code=400,
            detail="A valid filename is required."
        )

    if not safe_filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are allowed."
    
        )

    # --------------------------------------------------------
    # Read + size-limit the upload (cheap DoS mitigation - without
    # this, a single request could write an arbitrarily large file
    # to disk)
    # --------------------------------------------------------

    file_bytes = await file.read()

    if len(file_bytes) > MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum size is {MAX_UPLOAD_BYTES // (1024 * 1024)} MB.",
        )

    # --------------------------------------------------------
    # Save uploaded file
    #
    # Namespaced with a random prefix per upload, not just the raw
    # filename - two uploads sharing a filename (different
    # conversations, or the same conversation twice) would otherwise
    # silently overwrite each other's file on disk, corrupting
    # whichever attachment loses the race. The DB and FAISS index
    # still record the user-facing filename (safe_filename)
    # unchanged, so nothing else about the app's behavior changes.
    # --------------------------------------------------------

    stored_filename = f"{uuid.uuid4().hex}_{safe_filename}"
    file_path = UPLOAD_FOLDER / stored_filename

    with open(file_path, "wb") as f:
        f.write(file_bytes)

    # --------------------------------------------------------
    # Extract text
    # --------------------------------------------------------

    try:
        text = extract_text_from_pdf(file_path)
    except ValueError as e:
        # Remove invalid uploaded file
        if file_path.exists():
            file_path.unlink()

        raise HTTPException(
            status_code=400,
            detail=str(e)
        )

    except Exception as e:
        print("Unexpected PDF upload error:", e)

        if file_path.exists():
            file_path.unlink()

        raise HTTPException(
            status_code=500,
            detail="Unable to process the uploaded PDF."
        )

    # --------------------------------------------------------
    # Split into chunks
    # --------------------------------------------------------

    chunks = split_text(text)

    # --------------------------------------------------------
    # Add chunks to conversation-aware PDF index
    # --------------------------------------------------------

    build_pdf_index(
        chunks,
        safe_filename,
        conversation_id
    )

    # --------------------------------------------------------
    # Save attachment metadata
    # --------------------------------------------------------

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO attachments (
            conversation_id,
            filename,
            file_path,
            file_type
        )
        VALUES (?, ?, ?, ?)
        """,
        (
            (
                conversation_id,
                safe_filename,
                str(file_path),
                file.content_type,
            )
        ),
    )

    conn.commit()

    attachment_id = cursor.lastrowid

    conn.close()

    # --------------------------------------------------------
    # Response
    # --------------------------------------------------------

    return {
        "message": "PDF uploaded successfully",
        "filename": safe_filename,
        "chunks": len(chunks),
        "attachment_id": attachment_id,
        "conversation_id": conversation_id,
    }
    