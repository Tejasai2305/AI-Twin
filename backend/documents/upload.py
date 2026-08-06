from fastapi import APIRouter, UploadFile, File
import os

from backend.documents.pdf_service import extract_text_from_pdf
from backend.documents.chunking import split_text
from backend.documents.pdf_vector_store import build_pdf_index

router = APIRouter()

UPLOAD_FOLDER = "uploads"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@router.post("/upload-pdf")
async def upload_pdf(file: UploadFile = File(...)):

    file_path = os.path.join(UPLOAD_FOLDER, file.filename)

    with open(file_path, "wb") as f:
        f.write(await file.read())

    text = extract_text_from_pdf(file_path)

    chunks = split_text(text)

    build_pdf_index(chunks, file.filename)

    return {
        "message": "PDF uploaded successfully",
        "filename": file.filename,
        "chunks": len(chunks)
    }