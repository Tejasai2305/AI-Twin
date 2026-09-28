"""
Centralized database configuration (Feature 14 / 22 / 37).

Single place that decides which database driver is in use, based on
the DATABASE_URL environment variable:

  - Not set (default): SQLite, at the same path as before
    (AI_TWIN_DATA_DIR/notes.db). Local development is unaffected.
  - Set to a postgres:// or postgresql:// URL: PostgreSQL, for
    production deployment.

Every other module gets its connection through
backend.database.database.get_connection() - nothing outside this
file and database.py should need to know which driver is active.
"""

import os

DATABASE_URL = os.getenv("DATABASE_URL", "").strip()

IS_POSTGRES = DATABASE_URL.startswith("postgres://") or DATABASE_URL.startswith("postgresql://")

DRIVER = "postgres" if IS_POSTGRES else "sqlite"
