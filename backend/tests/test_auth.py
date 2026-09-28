def test_signup_creates_account(client):
    r = client.post("/auth/signup", json={"username": "alice", "password": "alicepass123"})
    assert r.status_code == 200
    body = r.json()
    assert "access_token" in body
    assert body["user"]["username"] == "alice"


def test_signup_duplicate_username_rejected(client):
    client.post("/auth/signup", json={"username": "bob", "password": "bobpass123"})
    r = client.post("/auth/signup", json={"username": "bob", "password": "different123"})
    assert r.status_code == 400


def test_login_correct_password(client):
    client.post("/auth/signup", json={"username": "carol", "password": "carolpass123"})
    r = client.post("/auth/login", json={"username": "carol", "password": "carolpass123"})
    assert r.status_code == 200
    assert "access_token" in r.json()


def test_login_wrong_password_rejected(client):
    client.post("/auth/signup", json={"username": "dave", "password": "davepass123"})
    r = client.post("/auth/login", json={"username": "dave", "password": "wrongpassword"})
    assert r.status_code == 401


def test_login_nonexistent_user_rejected(client):
    r = client.post("/auth/login", json={"username": "nobody", "password": "whatever123"})
    assert r.status_code == 401


def test_me_requires_token(client):
    r = client.get("/auth/me")
    assert r.status_code == 401


def test_me_rejects_garbage_token(client):
    r = client.get("/auth/me", headers={"Authorization": "Bearer not.a.real.token"})
    assert r.status_code == 401


def test_me_returns_correct_user(client, make_user):
    headers, user = make_user()
    r = client.get("/auth/me", headers=headers)
    assert r.status_code == 200
    assert r.json()["id"] == user["id"]
    assert r.json()["username"] == user["username"]


def test_password_never_returned(client, make_user):
    headers, _ = make_user()
    r = client.get("/auth/me", headers=headers)
    body = r.json()
    assert "password" not in body
    assert "password_hash" not in body
