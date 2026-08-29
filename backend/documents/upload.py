from fastapi import APIRouter, UploadFile, File, Form
import os
from pathlib import Path

from backend.documents.pdf_service import extract_text_from_pdf
from backend.documents.chunking import split_text
from backend.documents.pdf_vector_store import build_pdf_index
from backend.database.database import get_connection


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


@router.post("/upload-pdf")
async def upload_pdf(
    file: UploadFile = File(...),
    conversation_id: int = Form(...)
):

    # --------------------------------------------------------
    # Save uploaded file
    # --------------------------------------------------------

    file_path = UPLOAD_FOLDER / file.filename

    with open(file_path, "wb") as f:
        f.write(await file.read())

    # --------------------------------------------------------
    # Extract text
    # --------------------------------------------------------

    text = extract_text_from_pdf(
        file_path
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
        file.filename,
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
            conversation_id,
            file.filename,
            str(file_path),
            file.content_type,
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
        "filename": file.filename,
        "chunks": len(chunks),
        "attachment_id": attachment_id,
        "conversation_id": conversation_id,
    }