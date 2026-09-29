import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from backend.database.database import get_connection
from backend.auth.security import hash_password


RESET_TOKEN_EXPIRE_MINUTES = 30


def _hash_reset_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def create_password_reset_token(email: str):
    email = email.strip().lower()

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT id, email FROM users WHERE LOWER(email) = ?",
        (email,),
    )
    row = cursor.fetchone()

    if row is None:
        conn.close()
        return None

    token = secrets.token_urlsafe(48)
    token_hash = _hash_reset_token(token)
    expires_at = datetime.now(timezone.utc) + timedelta(
        minutes=RESET_TOKEN_EXPIRE_MINUTES
    )

    cursor.execute(
        """
        UPDATE users
        SET reset_token_hash = ?, reset_token_expires_at = ?
        WHERE id = ?
        """,
        (token_hash, expires_at.isoformat(), row[0]),
    )

    conn.commit()
    conn.close()

    return token


def reset_password(token: str, new_password: str) -> bool:
    if not token or not new_password:
        return False

    token_hash = _hash_reset_token(token)

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT id, reset_token_expires_at
        FROM users
        WHERE reset_token_hash = ?
        """,
        (token_hash,),
    )
    row = cursor.fetchone()

    if row is None:
        conn.close()
        return False

    try:
        expires_at = datetime.fromisoformat(str(row[1]).replace("Z", "+00:00"))
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
    except (ValueError, TypeError):
        conn.close()
        return False

    if datetime.now(timezone.utc) >= expires_at:
        conn.close()
        return False

    password_hash = hash_password(new_password)

    cursor.execute(
        """
        UPDATE users
        SET password_hash = ?,
            reset_token_hash = NULL,
            reset_token_expires_at = NULL
        WHERE id = ?
        """,
        (password_hash, row[0]),
    )

    conn.commit()
    conn.close()

    return True
