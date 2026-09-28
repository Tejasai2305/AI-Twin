def test_graph_reflects_memories(client, auth_headers):
    client.post(
        "/memory",
        json={"memory": "User knows Python.", "memory_type": "technical_skill"},
        headers=auth_headers,
    )

    r = client.get("/graph", headers=auth_headers)
    assert r.status_code == 200
    data = r.json()
    fact_nodes = [n for n in data["nodes"] if n["type"] == "fact"]
    assert any("Python" in n.get("label", "") for n in fact_nodes)


def test_graph_isolated_between_users(client, make_user):
    headers_a, _ = make_user()
    headers_b, _ = make_user()

    client.post("/memory", json={"memory": "Alice knows Rust.", "memory_type": "technical_skill"}, headers=headers_a)

    r = client.get("/graph", headers=headers_b)
    fact_nodes = [n for n in r.json()["nodes"] if n["type"] == "fact"]
    assert not any("Rust" in n.get("label", "") for n in fact_nodes)


def test_graph_summary(client, auth_headers):
    client.post("/memory", json={"memory": "User knows Go.", "memory_type": "technical_skill"}, headers=auth_headers)
    r = client.get("/graph/summary", headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["total_facts"] >= 1


def test_timeline_includes_memory_and_conversation_events(client, auth_headers):
    client.post("/conversation", json={"title": "Timeline test convo"}, headers=auth_headers)
    client.post("/memory", json={"memory": "User started a new hobby.", "memory_type": "personal"}, headers=auth_headers)

    r = client.get("/timeline", headers=auth_headers)
    assert r.status_code == 200
    types = {e["type"] for e in r.json()}
    assert "conversation" in types
    assert "memory" in types


def test_timeline_isolated_between_users(client, make_user):
    headers_a, _ = make_user()
    headers_b, _ = make_user()

    client.post("/conversation", json={"title": "Alice only convo"}, headers=headers_a)

    r = client.get("/timeline", headers=headers_b)
    titles = [e["title"] for e in r.json()]
    assert not any("Alice only convo" in t for t in titles)


def test_profile_builds_from_memories(client, auth_headers):
    client.post("/memory", json={"memory": "User's CGPA is 9.0.", "memory_type": "education"}, headers=auth_headers)
    client.post("/memory", json={"memory": "User knows JavaScript.", "memory_type": "technical_skill"}, headers=auth_headers)

    r = client.get("/profile", headers=auth_headers)
    assert r.status_code == 200
    body = r.json()
    labels = [s["label"] for s in body["sections"]]
    assert "Education" in labels
    assert "Technical Skills" in labels


def test_profile_reports_missing_sections_honestly(client, auth_headers):
    client.post("/memory", json={"memory": "User knows Ruby.", "memory_type": "technical_skill"}, headers=auth_headers)
    r = client.get("/profile", headers=auth_headers)
    missing_types = [s["type"] for s in r.json()["missing_sections"]]
    assert "education" in missing_types


def test_profile_isolated_between_users(client, make_user):
    headers_a, _ = make_user()
    headers_b, _ = make_user()

    client.post("/memory", json={"memory": "Alice's unique fact.", "memory_type": "personal"}, headers=headers_a)

    r = client.get("/profile", headers=headers_b)
    all_text = str(r.json())
    assert "Alice's unique fact" not in all_text
