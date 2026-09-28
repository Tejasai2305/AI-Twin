"""
Password hashing (Feature 21: "never store plaintext passwords") and
JWT issuing/verification.

Uses the bcrypt library directly rather than through passlib: newer
bcrypt releases dropped the __about__.__version__ attribute that
passlib's backend probes for, which throws on hash/verify with
current bcrypt versions. Calling bcrypt directly avoids that
dependency-compatibility trap entirely.

SECRET_KEY MUST come from the environment in any real deployment - the
fallback here is only so local development doesn't crash on a missing
.env, and is intentionally obviously insecure to discourage relying
on it.
"""

import os
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt

SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev-only-insecure-secret-change-me")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "43200"))  # 30 days

# bcrypt's underlying algorithm silently truncates inputs over 72 bytes;
# reject longer passwords explicitly rather than let it be silently ignored.
MAX_PASSWORD_BYTES = 72


def hash_password(password: str) -> str:
    if len(password.encode("utf-8")) > MAX_PASSWORD_BYTES:
        raise ValueError(f"Password must be at most {MAX_PASSWORD_BYTES} bytes.")
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def verify_password(plain_password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), password_hash.encode("utf-8"))
    except Exception:
        return False


def create_access_token(user_id: int, username: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": str(user_id),
        "username": username,
        "exp": expire,
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str):
    """Returns the payload dict, or None if the token is invalid/expired."""
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.PyJWTError:
        return None
