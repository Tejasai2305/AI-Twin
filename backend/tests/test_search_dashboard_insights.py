def test_global_search_finds_memory(client, auth_headers):
    client.post("/memory", json={"memory": "User loves rock climbing."}, headers=auth_headers)
    r = client.get("/search", params={"q": "climbing"}, headers=auth_headers)
    assert r.status_code == 200
    memories = r.json()["memories"]
    assert any("rock climbing" in m["memory"] for m in memories)


def test_global_search_isolated_between_users(client, make_user):
    headers_a, _ = make_user()
    headers_b, _ = make_user()

    client.post("/memory", json={"memory": "Alice's unique searchable fact."}, headers=headers_a)

    r = client.get("/search", params={"q": "unique searchable"}, headers=headers_b)
    assert r.json()["memories"] == []


def test_global_search_finds_conversation(client, auth_headers):
    client.post("/conversation", json={"title": "Discussing quantum computing"}, headers=auth_headers)
    r = client.get("/search", params={"q": "quantum"}, headers=auth_headers)
    titles = [c["title"] for c in r.json()["conversations"]]
    assert any("quantum" in t.lower() for t in titles)


def test_global_search_empty_query(client, auth_headers):
    r = client.get("/search", params={"q": ""}, headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["conversations"] == []
    assert r.json()["memories"] == []


def test_dashboard_totals_match_reality(client, auth_headers):
    client.post("/conversation", json={"title": "Dash test"}, headers=auth_headers)
    client.post("/memory", json={"memory": "Dashboard fact.", "memory_type": "technical_skill"}, headers=auth_headers)

    r = client.get("/dashboard", headers=auth_headers)
    assert r.status_code == 200
    totals = r.json()["totals"]
    assert totals["conversations"] >= 1
    assert totals["memories"] >= 1
    assert totals["skills"] >= 1


def test_dashboard_isolated_between_users(client, make_user):
    headers_a, _ = make_user()
    headers_b, _ = make_user()

    client.post("/conversation", json={"title": "Alice's convo"}, headers=headers_a)
    client.post("/memory", json={"memory": "Alice fact."}, headers=headers_a)

    r = client.get("/dashboard", headers=headers_b)
    totals = r.json()["totals"]
    assert totals["conversations"] == 0
    assert totals["memories"] == 0


def test_insights_flags_low_confidence_fact(client, auth_headers):
    client.post(
        "/memory",
        json={"memory": "User might like something vague.", "confidence": 0.2},
        headers=auth_headers,
    )
    r = client.get("/insights", headers=auth_headers)
    assert r.status_code == 200
    assert any(i["type"] == "low_confidence_facts" for i in r.json())


def test_insights_flags_profile_gap(client, auth_headers):
    client.post("/memory", json={"memory": "User knows Elixir.", "memory_type": "technical_skill"}, headers=auth_headers)
    r = client.get("/insights", headers=auth_headers)
    assert any(i["type"] == "profile_gap" for i in r.json())


def test_insights_isolated_between_users(client, make_user):
    headers_a, _ = make_user()
    headers_b, _ = make_user()

    client.post("/memory", json={"memory": "vague thing", "confidence": 0.1}, headers=headers_a)

    r = client.get("/insights", headers=headers_b)
    assert not any(i["type"] == "low_confidence_facts" for i in r.json())
