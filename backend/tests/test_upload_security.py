import io


def _pdf_bytes(content=b"%PDF-1.4 fake pdf content for testing"):
    return io.BytesIO(content)


def test_upload_requires_conversation_ownership(client, make_user):
    headers_a, _ = make_user()
    headers_b, _ = make_user()

    conv_a = client.post("/conversation", json={"title": "Alice"}, headers=headers_a).json()

    r = client.post(
        "/upload-pdf",
        files={"file": ("hijack.pdf", _pdf_bytes(), "application/pdf")},
        data={"conversation_id": conv_a["id"]},
        headers=headers_b,
    )
    assert r.status_code == 404


def test_upload_unauthenticated_cannot_target_owned_conversation(client, auth_headers):
    conv = client.post("/conversation", json={"title": "Owned"}, headers=auth_headers).json()

    r = client.post(
        "/upload-pdf",
        files={"file": ("anon.pdf", _pdf_bytes(), "application/pdf")},
        data={"conversation_id": conv["id"]},
    )
    assert r.status_code == 404


def test_upload_rejects_non_pdf_extension(client, auth_headers):
    conv = client.post("/conversation", json={"title": "Test"}, headers=auth_headers).json()

    r = client.post(
        "/upload-pdf",
        files={"file": ("not_a_pdf.txt", _pdf_bytes(), "text/plain")},
        data={"conversation_id": conv["id"]},
        headers=auth_headers,
    )
    assert r.status_code == 400


def test_upload_strips_path_traversal_from_filename(client, auth_headers, monkeypatch):
    conv = client.post("/conversation", json={"title": "Test"}, headers=auth_headers).json()

    # Mock PDF text extraction so this test doesn't need a real PDF parser
    import backend.documents.upload as upload_module
    monkeypatch.setattr(upload_module, "extract_text_from_pdf", lambda path: "fake extracted text")

    r = client.post(
        "/upload-pdf",
        files={"file": ("../../etc/passwd.pdf", _pdf_bytes(), "application/pdf")},
        data={"conversation_id": conv["id"]},
        headers=auth_headers,
    )
    assert r.status_code == 200
    # The stored/returned filename must never contain path separators
    assert "/" not in r.json()["filename"]
    assert ".." not in r.json()["filename"]


def test_two_uploads_with_same_filename_do_not_overwrite_each_other(client, auth_headers, monkeypatch):
    import backend.documents.upload as upload_module

    contents = iter(["first document content", "second document content"])
    monkeypatch.setattr(
        upload_module, "extract_text_from_pdf", lambda path: next(contents)
    )

    conv1 = client.post("/conversation", json={"title": "Conv 1"}, headers=auth_headers).json()
    conv2 = client.post("/conversation", json={"title": "Conv 2"}, headers=auth_headers).json()

    r1 = client.post(
        "/upload-pdf",
        files={"file": ("report.pdf", _pdf_bytes(b"AAA"), "application/pdf")},
        data={"conversation_id": conv1["id"]},
        headers=auth_headers,
    )
    r2 = client.post(
        "/upload-pdf",
        files={"file": ("report.pdf", _pdf_bytes(b"BBB"), "application/pdf")},
        data={"conversation_id": conv2["id"]},
        headers=auth_headers,
    )
    assert r1.status_code == 200
    assert r2.status_code == 200

    from backend.database.database import get_connection
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT file_path FROM attachments WHERE conversation_id IN (?, ?)",
        (conv1["id"], conv2["id"]),
    )
    paths = [row[0] for row in cursor.fetchall()]
    conn.close()

    assert len(paths) == 2
    assert paths[0] != paths[1]

    import os
    assert all(os.path.exists(p) for p in paths)
    contents_on_disk = [open(p, "rb").read() for p in paths]
    assert b"AAA" in contents_on_disk[0] or b"AAA" in contents_on_disk[1]
    assert b"BBB" in contents_on_disk[0] or b"BBB" in contents_on_disk[1]
    assert contents_on_disk[0] != contents_on_disk[1]


def test_upload_rejects_oversized_file(client, auth_headers):
    import backend.documents.upload as upload_module

    conv = client.post("/conversation", json={"title": "Big file"}, headers=auth_headers).json()

    oversized = b"0" * (upload_module.MAX_UPLOAD_BYTES + 1)

    r = client.post(
        "/upload-pdf",
        files={"file": ("huge.pdf", io.BytesIO(oversized), "application/pdf")},
        data={"conversation_id": conv["id"]},
        headers=auth_headers,
    )
    assert r.status_code == 400
