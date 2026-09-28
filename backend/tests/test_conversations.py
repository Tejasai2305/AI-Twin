def test_create_conversation(client, auth_headers):
    r = client.post("/conversation", json={"title": "My first chat"}, headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["title"] == "My first chat"
    assert "id" in r.json()


def test_list_conversations_scoped_to_owner(client, make_user):
    headers_a, _ = make_user()
    headers_b, _ = make_user()

    client.post("/conversation", json={"title": "Alice conv"}, headers=headers_a)
    client.post("/conversation", json={"title": "Bob conv"}, headers=headers_b)

    r = client.get("/conversations", headers=headers_a)
    titles = [c["title"] for c in r.json()]
    assert "Alice conv" in titles
    assert "Bob conv" not in titles


def test_get_conversation_by_id(client, auth_headers):
    created = client.post("/conversation", json={"title": "Details test"}, headers=auth_headers).json()
    r = client.get(f"/conversation/{created['id']}", headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["title"] == "Details test"


def test_get_other_users_conversation_returns_404(client, make_user):
    headers_a, _ = make_user()
    headers_b, _ = make_user()

    conv = client.post("/conversation", json={"title": "Private"}, headers=headers_a).json()

    r = client.get(f"/conversation/{conv['id']}", headers=headers_b)
    assert r.status_code == 404


def test_update_conversation_title(client, auth_headers):
    conv = client.post("/conversation", json={"title": "Old title"}, headers=auth_headers).json()
    r = client.put(f"/conversation/{conv['id']}", json={"title": "New title"}, headers=auth_headers)
    assert r.status_code == 200

    r2 = client.get(f"/conversation/{conv['id']}", headers=auth_headers)
    assert r2.json()["title"] == "New title"


def test_delete_conversation(client, auth_headers):
    conv = client.post("/conversation", json={"title": "To delete"}, headers=auth_headers).json()
    r = client.delete(f"/conversation/{conv['id']}", headers=auth_headers)
    assert r.status_code == 200

    r2 = client.get(f"/conversation/{conv['id']}", headers=auth_headers)
    assert r2.status_code == 404


def test_search_conversations_by_title(client, auth_headers):
    client.post("/conversation", json={"title": "Talking about FastAPI"}, headers=auth_headers)
    client.post("/conversation", json={"title": "Unrelated topic"}, headers=auth_headers)

    r = client.get("/conversations/search", params={"q": "FastAPI"}, headers=auth_headers)
    assert r.status_code == 200
    titles = [c["title"] for c in r.json()]
    assert any("FastAPI" in t for t in titles)
    assert "Unrelated topic" not in titles


def test_update_other_users_conversation_returns_404(client, make_user):
    headers_a, _ = make_user()
    headers_b, _ = make_user()
    conv = client.post("/conversation", json={"title": "Private"}, headers=headers_a).json()
    r = client.put(f"/conversation/{conv['id']}", json={"title": "Hijacked"}, headers=headers_b)
    assert r.status_code == 404


def test_delete_other_users_conversation_returns_404(client, make_user):
    headers_a, _ = make_user()
    headers_b, _ = make_user()
    conv = client.post("/conversation", json={"title": "Private"}, headers=headers_a).json()
    r = client.delete(f"/conversation/{conv['id']}", headers=headers_b)
    assert r.status_code == 404

    # Confirm it's still there for the real owner
    r2 = client.get(f"/conversation/{conv['id']}", headers=headers_a)
    assert r2.status_code == 200


def test_get_nonexistent_conversation_404(client, auth_headers):
    r = client.get("/conversation/999999", headers=auth_headers)
    assert r.status_code == 404
