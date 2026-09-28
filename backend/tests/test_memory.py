def test_create_and_list_memory(client, auth_headers):
    r = client.post(
        "/memory",
        json={"memory": "User knows Python.", "importance": 8, "memory_type": "technical_skill"},
        headers=auth_headers,
    )
    assert r.status_code == 200

    r2 = client.get("/memories", headers=auth_headers)
    assert any(m["memory"] == "User knows Python." for m in r2.json())


def test_memories_isolated_between_users(client, make_user):
    headers_a, _ = make_user()
    headers_b, _ = make_user()

    client.post("/memory", json={"memory": "Alice's secret fact."}, headers=headers_a)
    client.post("/memory", json={"memory": "Bob's secret fact."}, headers=headers_b)

    r_a = client.get("/memories", headers=headers_a)
    r_b = client.get("/memories", headers=headers_b)

    a_texts = [m["memory"] for m in r_a.json()]
    b_texts = [m["memory"] for m in r_b.json()]

    assert "Alice's secret fact." in a_texts
    assert "Bob's secret fact." not in a_texts
    assert "Bob's secret fact." in b_texts
    assert "Alice's secret fact." not in b_texts


def test_unauthenticated_cannot_see_owned_memories(client, auth_headers):
    client.post("/memory", json={"memory": "Owned fact."}, headers=auth_headers)
    r = client.get("/memories")
    assert all(m["memory"] != "Owned fact." for m in r.json())


def test_get_memory_detail(client, auth_headers):
    client.post("/memory", json={"memory": "Detail test fact."}, headers=auth_headers)
    memories = client.get("/memories/detailed", headers=auth_headers).json()
    memory_id = memories[0]["id"]

    r = client.get(f"/memory/{memory_id}/detail", headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["memory"] == "Detail test fact."


def test_cannot_access_other_users_memory_by_id(client, make_user):
    headers_a, _ = make_user()
    headers_b, _ = make_user()

    client.post("/memory", json={"memory": "Alice's private fact."}, headers=headers_a)
    memory_id = client.get("/memories/detailed", headers=headers_a).json()[0]["id"]

    r = client.get(f"/memory/{memory_id}/detail", headers=headers_b)
    assert r.status_code == 404


def test_update_memory(client, auth_headers):
    client.post("/memory", json={"memory": "Original text.", "importance": 5}, headers=auth_headers)
    memory_id = client.get("/memories/detailed", headers=auth_headers).json()[0]["id"]

    r = client.put(
        f"/memory/{memory_id}",
        json={"memory": "Updated text.", "importance": 7},
        headers=auth_headers,
    )
    assert r.status_code == 200

    detail = client.get(f"/memory/{memory_id}/detail", headers=auth_headers).json()
    assert detail["memory"] == "Updated text."
    assert detail["importance"] == 7


def test_deactivate_and_reactivate_memory(client, auth_headers):
    client.post("/memory", json={"memory": "Toggle me."}, headers=auth_headers)
    memory_id = client.get("/memories/detailed", headers=auth_headers).json()[0]["id"]

    r = client.post(f"/memory/{memory_id}/deactivate", headers=auth_headers)
    assert r.status_code == 200

    active = client.get("/memories/detailed", headers=auth_headers).json()
    assert all(m["id"] != memory_id for m in active)

    with_inactive = client.get(
        "/memories/detailed", params={"include_inactive": True}, headers=auth_headers
    ).json()
    assert any(m["id"] == memory_id and m["is_active"] is False for m in with_inactive)

    client.post(f"/memory/{memory_id}/reactivate", headers=auth_headers)
    active_again = client.get("/memories/detailed", headers=auth_headers).json()
    assert any(m["id"] == memory_id for m in active_again)


def test_delete_memory(client, auth_headers):
    client.post("/memory", json={"memory": "Delete me."}, headers=auth_headers)
    memory_id = client.get("/memories/detailed", headers=auth_headers).json()[0]["id"]

    r = client.delete(f"/memory/{memory_id}", headers=auth_headers)
    assert r.status_code == 200

    r2 = client.get(f"/memory/{memory_id}/detail", headers=auth_headers)
    assert r2.status_code == 404


def test_memory_types_endpoint(client):
    r = client.get("/memory/types")
    assert r.status_code == 200
    assert "education" in r.json()
    assert "technical_skill" in r.json()


def test_reject_unknown_memory_type_filter(client, auth_headers):
    r = client.get("/memories/detailed", params={"memory_type": "not_a_real_type"}, headers=auth_headers)
    assert r.status_code == 400


def test_contradiction_supersedes_old_value(client, make_user, mock_gemini):
    headers, user = make_user()
    mock_gemini(lambda prompt: '{"remember": false}')

    # First fact
    client.post(
        "/memory",
        json={"memory": "User CGPA is 8.8.", "memory_type": "education"},
        headers=headers,
    )

    old_id = client.get("/memories/detailed", headers=headers).json()[0]["id"]

    def decide_with_real_id(prompt):
        return f'{{"action": "update", "memory_id": {old_id}}}'

    mock_gemini(decide_with_real_id)

    from backend.services.memory_conflict_detector import save_memory_with_conflict_check
    from backend.services.memory_service import get_memory_detail

    result = save_memory_with_conflict_check(
        "User CGPA is 8.97.",
        importance=7,
        memory_type="education",
        confidence=0.9,
        user_id=user["id"],
    )

    assert result["action"] == "updated"
    new_id = result["memory_id"]

    old_detail = get_memory_detail(old_id)
    new_detail = get_memory_detail(new_id)

    assert old_detail["is_active"] is False
    assert old_detail["valid_until"] is not None
    assert new_detail["is_active"] is True
    assert new_detail["memory"] == "User CGPA is 8.97."
    assert new_detail["supersedes_id"] == old_id


def test_memory_timeline_shows_full_chain(client, make_user, mock_gemini):
    headers, user = make_user()
    client.post(
        "/memory",
        json={"memory": "User CGPA is 8.8.", "memory_type": "education"},
        headers=headers,
    )
    old_id = client.get("/memories/detailed", headers=headers).json()[0]["id"]

    def decide(prompt):
        return f'{{"action": "update", "memory_id": {old_id}}}'
    mock_gemini(decide)

    from backend.services.memory_conflict_detector import save_memory_with_conflict_check
    save_memory_with_conflict_check("User CGPA is 8.97.", memory_type="education", user_id=user["id"])

    r = client.get(f"/memory/{old_id}/timeline", headers=headers)
    assert r.status_code == 200
    chain = r.json()
    assert len(chain) == 2
    assert chain[0]["memory"] == "User CGPA is 8.8."
    assert chain[1]["memory"] == "User CGPA is 8.97."


def test_contradictions_feed(client, make_user, mock_gemini):
    headers, user = make_user()
    client.post(
        "/memory",
        json={"memory": "User CGPA is 8.8.", "memory_type": "education"},
        headers=headers,
    )
    old_id = client.get("/memories/detailed", headers=headers).json()[0]["id"]

    def decide(prompt):
        return f'{{"action": "update", "memory_id": {old_id}}}'
    mock_gemini(decide)

    from backend.services.memory_conflict_detector import save_memory_with_conflict_check
    save_memory_with_conflict_check("User CGPA is 8.97.", memory_type="education", user_id=user["id"])

    r = client.get("/memory/contradictions", headers=headers)
    assert r.status_code == 200
    contradictions = r.json()
    assert len(contradictions) == 1
    assert contradictions[0]["previous_value"] == "User CGPA is 8.8."
    assert contradictions[0]["current_value"] == "User CGPA is 8.97."


def test_semantic_memory_search(client, auth_headers):
    client.post("/memory", json={"memory": "User loves hiking on weekends."}, headers=auth_headers)
    r = client.get("/memory/search", params={"query": "hiking"}, headers=auth_headers)
    assert r.status_code == 200


def test_empty_search_query_rejected(client, auth_headers):
    r = client.get("/memory/search", params={"query": ""}, headers=auth_headers)
    assert r.status_code == 400
