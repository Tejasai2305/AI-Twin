from fastapi import APIRouter, Depends, HTTPException

from backend.auth.dependencies import get_optional_user
from backend.documents.document_service import (
    list_documents,
    get_document,
    delete_document,
)

router = APIRouter()


def _assert_owned(document_id, current_user):
    doc = get_document(document_id)
    if doc is None:
        raise HTTPException(status_code=404, detail="Document not found.")
    if current_user is not None and doc["owner_user_id"] != current_user["id"]:
        raise HTTPException(status_code=404, detail="Document not found.")
    return doc


@router.get("/documents")
def get_documents(conversation_id: int | None = None, current_user=Depends(get_optional_user)):
    try:
        user_id = current_user["id"] if current_user else None
        return list_documents(conversation_id=conversation_id, user_id=user_id)
    except Exception as e:
        print("Document listing error:", e)
        raise HTTPException(status_code=500, detail="Unable to list documents.")


@router.get("/documents/{document_id}")
def get_document_route(document_id: int, current_user=Depends(get_optional_user)):
    return _assert_owned(document_id, current_user)


@router.delete("/documents/{document_id}")
def delete_document_route(document_id: int, current_user=Depends(get_optional_user)):
    _assert_owned(document_id, current_user)
    doc = delete_document(document_id)
    return {"message": f"Deleted {doc['filename']} and its indexed content."}
