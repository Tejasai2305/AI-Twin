def _make_conversation(client, headers, title="Doc test"):
    return client.post("/conversation", json={"title": title}, headers=headers).json()


def _seed_document(conversation_id, filename="resume.pdf"):
    """
    Directly inserts an attachment row + a fake indexed chunk,
    bypassing the real PDF upload/extraction pipeline (which needs an
    actual PDF file) - this suite is testing the Document Center's
    listing/deletion/isolation logic, not PDF text extraction itself.
    """
    from backend.database.database import get_connection
    from backend.documents.pdf_vector_store import build_pdf_index

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO attachments(conversation_id, filename, file_path, file_type) VALUES (?, ?, ?, ?)",
        (conversation_id, filename, f"/tmp/{filename}", "application/pdf"),
    )
    attachment_id = cursor.lastrowid
    conn.commit()
    conn.close()

    build_pdf_index([f"Sample content from {filename}."], filename, conversation_id)

    return attachment_id


def test_list_documents_scoped_to_owner(client, make_user):
    headers_a, _ = make_user()
    headers_b, _ = make_user()

    conv_a = _make_conversation(client, headers_a)
    conv_b = _make_conversation(client, headers_b)

    _seed_document(conv_a["id"], "alice_resume.pdf")
    _seed_document(conv_b["id"], "bob_resume.pdf")

    r = client.get("/documents", headers=headers_a)
    filenames = [d["filename"] for d in r.json()]
    assert "alice_resume.pdf" in filenames
    assert "bob_resume.pdf" not in filenames


def test_document_shows_indexed_status(client, auth_headers):
    conv = _make_conversation(client, auth_headers)
    _seed_document(conv["id"], "indexed.pdf")

    r = client.get("/documents", headers=auth_headers)
    doc = next(d for d in r.json() if d["filename"] == "indexed.pdf")
    assert doc["indexed"] is True
    assert doc["chunk_count"] >= 1


def test_cannot_access_other_users_document(client, make_user):
    headers_a, _ = make_user()
    headers_b, _ = make_user()

    conv_a = _make_conversation(client, headers_a)
    attachment_id = _seed_document(conv_a["id"], "private.pdf")

    r = client.get(f"/documents/{attachment_id}", headers=headers_b)
    assert r.status_code == 404


def test_delete_document_removes_it_and_its_index(client, auth_headers):
    from backend.documents.pdf_vector_store import search_pdf

    conv = _make_conversation(client, auth_headers)
    attachment_id = _seed_document(conv["id"], "deleteme.pdf")

    results_before = search_pdf("Sample content", conv["id"])
    assert len(results_before) >= 1

    r = client.delete(f"/documents/{attachment_id}", headers=auth_headers)
    assert r.status_code == 200

    r2 = client.get(f"/documents/{attachment_id}", headers=auth_headers)
    assert r2.status_code == 404

    results_after = search_pdf("Sample content", conv["id"])
    assert results_after == []
