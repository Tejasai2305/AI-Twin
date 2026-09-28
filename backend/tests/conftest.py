"""
Shared fixtures for the AI-Twin backend test suite.

Design notes, since this codebase computes file paths (DB_NAME,
FAISS index paths) once at import time from AI_TWIN_DATA_DIR:
  - AI_TWIN_DATA_DIR is pointed at a temp directory ONCE, before any
    backend module is imported, so every path in the app resolves
    against it for the whole test session (matches how the app
    actually runs - one shared DB - rather than fighting the
    architecture with per-test directories).
  - Isolation between tests is achieved by truncating every table
    and resetting the in-memory FAISS globals before each test,
    not by swapping directories.
  - JWT_SECRET_KEY is fixed so tokens are stable across the run and
    tests never depend on the insecure dev-only fallback.
"""

import os
import tempfile

_TEST_DATA_DIR = tempfile.mkdtemp(prefix="ai_twin_test_")
os.environ["AI_TWIN_DATA_DIR"] = _TEST_DATA_DIR
os.environ["JWT_SECRET_KEY"] = "test-suite-fixed-secret-not-for-production"
os.environ.setdefault("DATABASE_URL", "")  # force SQLite path for tests

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.database.database import create_table, get_connection


def _build_test_app() -> FastAPI:
    """
    Assembles the same routers as backend/main.py, without running
    main.py's own module-level startup (which touches external
    clients like Gemini/Tavily) - keeps tests hermetic.
    """
    from backend.routers.conversations import router as conversations_router
    from backend.routers.notes import router as notes_router
    from backend.routers.memory import router as memory_router
    from backend.routers.graph import router as graph_router
    from backend.routers.timeline import router as timeline_router
    from backend.routers.profile import router as profile_router
    from backend.routers.documents import router as documents_router
    from backend.routers.search import router as search_router
    from backend.routers.dashboard import router as dashboard_router
    from backend.routers.insights import router as insights_router
    from backend.routers.decision import router as decision_router
    from backend.routers.auth import router as auth_router
    from backend.documents.upload import router as upload_router

    app = FastAPI()
    for r in [
        auth_router, conversations_router, notes_router, memory_router,
        graph_router, timeline_router, profile_router, documents_router,
        search_router, dashboard_router, insights_router, decision_router,
        upload_router,
    ]:
        app.include_router(r)

    @app.get("/health")
    def health():
        return {"status": "ok"}

    return app


_APP = _build_test_app()


def _reset_state():
    """Truncate every table and clear in-memory index globals."""
    create_table()

    conn = get_connection()
    cursor = conn.cursor()
    for table in [
        "memory_history", "memories", "attachments", "messages",
        "conversations", "notes", "sessions", "users",
    ]:
        try:
            cursor.execute(f"DELETE FROM {table}")
        except Exception:
            pass  # table may not exist depending on schema version
    conn.commit()
    conn.close()

    import backend.embeddings.memory_vector_store as mvs
    mvs.index = None
    mvs.memory_list = []

    import backend.documents.pdf_vector_store as pvs
    pvs.pdf_index = None
    pvs.pdf_chunks = []

    for path_attr in ("INDEX_PATH", "MEMORY_PATH"):
        path = getattr(mvs, path_attr, None)
        if path and path.exists():
            path.unlink()

    pdf_index_path = getattr(pvs, "PDF_INDEX_PATH", None)
    if pdf_index_path and pdf_index_path.exists():
        pdf_index_path.unlink()


@pytest.fixture(autouse=True)
def clean_state():
    """Runs before every test: fresh tables, fresh in-memory indexes."""
    _reset_state()
    yield


@pytest.fixture
def client():
    return TestClient(_APP)


@pytest.fixture
def make_user(client):
    """Factory: make_user() -> (headers, user_dict). Each call signs up
    a fresh, randomly-named user so tests can create as many
    independent accounts as they need."""
    import uuid

    def _make():
        username = f"user_{uuid.uuid4().hex[:12]}"
        res = client.post(
            "/auth/signup",
            json={"username": username, "password": "testpassword123"},
        )
        assert res.status_code == 200, res.text
        token = res.json()["access_token"]
        user = res.json()["user"]
        headers = {"Authorization": f"Bearer {token}"}
        return headers, user

    return _make


@pytest.fixture
def auth_headers(make_user):
    """A single ready-to-use authenticated user's headers."""
    headers, _ = make_user()
    return headers


@pytest.fixture
def mock_gemini(monkeypatch):
    """
    Factory fixture: mock_gemini(fn) replaces ask_gemini everywhere
    it's already been imported (extractor, ai_memory_manager, decision
    service all import it at module load, so each is patched
    individually - patching only gemini_service.ask_gemini would miss
    those already-bound references).
    """
    def _apply(fn):
        import backend.ai.gemini_service as gemini_service
        monkeypatch.setattr(gemini_service, "ask_gemini", fn)

        import backend.ai.memory_extractor as extractor
        monkeypatch.setattr(extractor, "ask_gemini", fn)

        import backend.services.ai_memory_manager as manager
        if hasattr(manager, "ask_gemini"):
            monkeypatch.setattr(manager, "ask_gemini", fn)

        import backend.services.decision_service as decision
        if hasattr(decision, "ask_gemini"):
            monkeypatch.setattr(decision, "ask_gemini", fn)

        import backend.services.pipeline.llm_stage as llm_stage
        if hasattr(llm_stage, "ask_gemini"):
            monkeypatch.setattr(llm_stage, "ask_gemini", fn)

        import backend.services.title_generator as title_generator
        if hasattr(title_generator, "ask_gemini"):
            monkeypatch.setattr(title_generator, "ask_gemini", fn)

        import backend.agent.tool_router as tool_router
        if hasattr(tool_router, "ask_gemini"):
            monkeypatch.setattr(tool_router, "ask_gemini", fn)

        import backend.tools.search as web_search_tool
        if hasattr(web_search_tool, "ask_gemini"):
            monkeypatch.setattr(web_search_tool, "ask_gemini", fn)

    return _apply


@pytest.fixture
def mock_gemini_stream(monkeypatch):
    """
    Companion to mock_gemini for the streaming endpoints
    (/ask-stream, /regenerate-stream, /edit-message-stream), which
    call ask_gemini_stream (a generator) rather than ask_gemini.
    routers/notes.py imports it directly, so it's patched there too.
    fn should be a callable taking (prompt) and returning an iterable
    of string chunks.
    """
    def _apply(fn):
        import backend.ai.gemini_service as gemini_service
        monkeypatch.setattr(gemini_service, "ask_gemini_stream", fn)

        import backend.routers.notes as notes
        if hasattr(notes, "ask_gemini_stream"):
            monkeypatch.setattr(notes, "ask_gemini_stream", fn)

    return _apply
