import sqlite3
import os
from pathlib import Path

from backend.database.config import IS_POSTGRES, DATABASE_URL

BASE_DIR = Path(__file__).resolve().parent.parent.parent

DATA_DIR = Path(
    os.getenv("AI_TWIN_DATA_DIR", str(BASE_DIR))
)

DATA_DIR.mkdir(parents=True, exist_ok=True)

DB_NAME = DATA_DIR / "notes.db"


def get_connection():
    if IS_POSTGRES:
        # Imported lazily so psycopg2 is only required in production
        # deployments that actually set DATABASE_URL - local SQLite
        # development never needs it installed.
        import psycopg2
        from backend.database.pg_compat import PGConnectionShim

        real_conn = psycopg2.connect(DATABASE_URL)
        return PGConnectionShim(real_conn)

    conn = sqlite3.connect(
        DB_NAME,
        timeout=10
    )

    conn.execute("PRAGMA foreign_keys = ON")

    return conn


def create_table():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL UNIQUE,
        email TEXT UNIQUE,
        password_hash TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS notes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        content TEXT NOT NULL
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS conversations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        user_id INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        conversation_id INTEGER NOT NULL,
        role TEXT NOT NULL,
        content TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (conversation_id) REFERENCES conversations(id)
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS memories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        memory TEXT NOT NULL,
        importance INTEGER DEFAULT 5,
        memory_type TEXT DEFAULT 'other',
        source TEXT DEFAULT 'conversation',
        source_reference TEXT,
        confidence REAL DEFAULT 0.7,
        evidence TEXT,
        is_active INTEGER DEFAULT 1,
        valid_from TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        valid_until TIMESTAMP,
        supersedes_id INTEGER,
        user_id INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS memory_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        memory_id INTEGER NOT NULL,
        old_memory TEXT,
        new_memory TEXT NOT NULL,
        action TEXT NOT NULL,
        changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (memory_id) REFERENCES memories(id)
    )
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS attachments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        conversation_id INTEGER NOT NULL,
        message_id INTEGER,
        filename TEXT NOT NULL,
        file_path TEXT NOT NULL,
        file_type TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (conversation_id) REFERENCES conversations(id)
    )
    """)

    conn.commit()
    conn.close()

    migrate_users_table()
    migrate_memories_table()
    migrate_conversations_table()
    migrate_attachments_table()


def migrate_users_table():
    """Additive migration for password-reset fields."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("PRAGMA table_info(users)")
    existing_columns = {row[1] for row in cursor.fetchall()}

    columns_to_add = {
        "reset_token_hash": "TEXT",
        "reset_token_expires_at": "TIMESTAMP",
    }

    for column, definition in columns_to_add.items():
        if column not in existing_columns:
            cursor.execute(
                f"ALTER TABLE users ADD COLUMN {column} {definition}"
            )
            print(f"[migration] added users.{column}")

    conn.commit()
    conn.close()

def migrate_attachments_table():
    """
    Additive migration: adds message_id to attachments for installs
    predating it. Without this column, attach_pending_files_to_message()
    in routers/notes.py (called on every /ask and /ask-stream request)
    fails with 'no such column: message_id' - a pre-existing bug this
    closes, not something introduced by the auth/isolation work.
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("PRAGMA table_info(attachments)")
    existing_columns = {row[1] for row in cursor.fetchall()}

    if "message_id" not in existing_columns:
        cursor.execute("ALTER TABLE attachments ADD COLUMN message_id INTEGER")
        print("[migration] added attachments.message_id")

    conn.commit()
    conn.close()


def migrate_conversations_table():
    """Additive migration: adds user_id to conversations for pre-auth installs."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("PRAGMA table_info(conversations)")
    existing_columns = {row[1] for row in cursor.fetchall()}

    if "user_id" not in existing_columns:
        cursor.execute("ALTER TABLE conversations ADD COLUMN user_id INTEGER")
        print("[migration] added conversations.user_id")

    conn.commit()
    conn.close()


def migrate_memories_table():
    """
    Additive, non-destructive migration for pre-existing 'memories'
    tables that predate the confidence/evidence/temporal columns.

    Uses ALTER TABLE ... ADD COLUMN only. Never drops or rewrites
    existing rows. Safe to run on every startup.
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("PRAGMA table_info(memories)")
    existing_columns = {row[1] for row in cursor.fetchall()}

    columns_to_add = {
        "memory_type": "TEXT DEFAULT 'other'",
        "source": "TEXT DEFAULT 'conversation'",
        "source_reference": "TEXT",
        "confidence": "REAL DEFAULT 0.7",
        "evidence": "TEXT",
        "is_active": "INTEGER DEFAULT 1",
        "valid_from": "TIMESTAMP",
        "valid_until": "TIMESTAMP",
        "created_at": "TIMESTAMP",
        "updated_at": "TIMESTAMP",
        "supersedes_id": "INTEGER",
        "user_id": "INTEGER",
    }

    for column, definition in columns_to_add.items():
        if column not in existing_columns:
            cursor.execute(
                f"ALTER TABLE memories ADD COLUMN {column} {definition}"
            )
            print(f"[migration] added memories.{column}")

    # Backfill NULL timestamps on rows that existed before this migration,
    # so old memories don't show blank dates in the Memory Center UI.
    cursor.execute("""
        UPDATE memories
        SET created_at = CURRENT_TIMESTAMP
        WHERE created_at IS NULL
    """)
    cursor.execute("""
        UPDATE memories
        SET updated_at = CURRENT_TIMESTAMP
        WHERE updated_at IS NULL
    """)
    cursor.execute("""
        UPDATE memories
        SET valid_from = CURRENT_TIMESTAMP
        WHERE valid_from IS NULL
    """)

    conn.commit()
    conn.close()


if __name__ == "__main__":
    create_table()
    print("Database and tables created successfully.")

