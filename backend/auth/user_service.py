from backend.database.database import get_connection
from backend.auth.security import hash_password, verify_password


def create_user(username: str, password: str, email: str = None):
    username = username.strip()

    if not username or not password:
        raise ValueError("Username and password are required.")

    if len(password) < 8:
        raise ValueError("Password must be at least 8 characters.")

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
    if cursor.fetchone():
        conn.close()
        raise ValueError("That username is already taken.")

    cursor.execute(
        "INSERT INTO users(username, email, password_hash) VALUES (?, ?, ?)",
        (username, email, hash_password(password)),
    )
    conn.commit()
    user_id = cursor.lastrowid
    conn.close()

    return {"id": user_id, "username": username, "email": email}


def authenticate_user(username: str, password: str):
    """Returns the user dict on success, or None on invalid credentials."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, username, email, password_hash FROM users WHERE username = ?",
        (username.strip(),),
    )
    row = cursor.fetchone()
    conn.close()

    if row is None:
        return None

    user_id, db_username, email, password_hash = row

    if not verify_password(password, password_hash):
        return None

    return {"id": user_id, "username": db_username, "email": email}


def get_user_by_id(user_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, username, email, created_at FROM users WHERE id = ?",
        (user_id,),
    )
    row = cursor.fetchone()
    conn.close()

    if row is None:
        return None

    return {"id": row[0], "username": row[1], "email": row[2], "created_at": row[3]}
