def _make_conversation(client, headers, title="Chat test"):
    return client.post("/conversation", json={"title": title}, headers=headers).json()


def test_ask_requires_existing_conversation(client, auth_headers, mock_gemini):
    mock_gemini(lambda prompt: '{"remember": false}')
    r = client.post("/ask", json={"conversation_id": 999999, "question": "Hello"}, headers=auth_headers)
    assert r.status_code == 404


def test_ask_rejects_empty_question(client, auth_headers):
    conv = _make_conversation(client, auth_headers)
    r = client.post("/ask", json={"conversation_id": conv["id"], "question": ""}, headers=auth_headers)
    assert r.status_code == 422


def test_ask_in_own_conversation_succeeds(client, auth_headers, mock_gemini):
    mock_gemini(lambda prompt: '{"remember": false}')
    conv = _make_conversation(client, auth_headers)
    r = client.post("/ask", json={"conversation_id": conv["id"], "question": "Hello there"}, headers=auth_headers)
    assert r.status_code == 200
    assert "answer" in r.json()


def test_cannot_ask_into_another_users_conversation(client, make_user, mock_gemini):
    mock_gemini(lambda prompt: '{"remember": false}')
    headers_a, _ = make_user()
    headers_b, _ = make_user()

    conv_a = _make_conversation(client, headers_a, "Alice private")

    r = client.post(
        "/ask",
        json={"conversation_id": conv_a["id"], "question": "Hijack attempt"},
        headers=headers_b,
    )
    assert r.status_code == 404


def test_unauthenticated_cannot_ask_into_owned_conversation(client, auth_headers, mock_gemini):
    mock_gemini(lambda prompt: '{"remember": false}')
    conv = _make_conversation(client, auth_headers)

    r = client.post("/ask", json={"conversation_id": conv["id"], "question": "anonymous"})
    assert r.status_code == 404


def test_chat_extracts_and_saves_memory_to_correct_owner(client, make_user, mock_gemini):
    headers_a, user_a = make_user()
    headers_b, _ = make_user()

    def fake_gemini(prompt):
        if "memory extractor" in prompt.lower():
            return '{"remember": true, "memory": "User CGPA is 8.8.", "memory_type": "education", "confidence": 0.9}'
        return '{"action": "add"}'

    mock_gemini(fake_gemini)

    conv_a = _make_conversation(client, headers_a, "Alice chat")
    client.post(
        "/ask",
        json={"conversation_id": conv_a["id"], "question": "My CGPA is 8.8."},
        headers=headers_a,
    )

    # Alice sees her own extracted memory
    r_a = client.get("/memories/detailed", headers=headers_a)
    assert any("8.8" in m["memory"] for m in r_a.json())

    # Bob does not see Alice's chat-extracted memory
    r_b = client.get("/memories/detailed", headers=headers_b)
    assert not any("8.8" in m["memory"] for m in r_b.json())


def test_chat_retrieval_does_not_leak_across_users(client, make_user, mock_gemini):
    headers_a, user_a = make_user()
    headers_b, user_b = make_user()

    # Seed each user with a distinct fact directly (no extraction needed)
    client.post("/memory", json={"memory": "Alice's favorite color is teal.", "memory_type": "preference"}, headers=headers_a)
    client.post("/memory", json={"memory": "Bob's favorite color is maroon.", "memory_type": "preference"}, headers=headers_b)

    mock_gemini(lambda prompt: '{"remember": false}')

    conv_a = _make_conversation(client, headers_a, "Alice color chat")
    r = client.post(
        "/ask",
        json={"conversation_id": conv_a["id"], "question": "What is my favorite color?"},
        headers=headers_a,
    )
    assert r.status_code == 200
    # We can't assert on the mocked LLM's final answer text (it's not
    # wired to actually read the prompt in this mock), but we CAN
    # assert the retrieval that fed the prompt was correctly scoped
    # by checking memory search directly.
    from backend.embeddings.memory_vector_store import search_memory
    results = search_memory("favorite color", user_id=user_a["id"])
    assert any("teal" in r for r in results)
    assert not any("maroon" in r for r in results)
