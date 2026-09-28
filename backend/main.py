from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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

from backend.startup import initialize

from backend.services.memory_service import rebuild_memory_index_from_db
from backend.embeddings.memory_vector_store import (
    build_memory_index,
    load_memory_index,
)


app = FastAPI()

import os

# -----------------------------
# CORS
# -----------------------------

# CORS_ORIGINS: comma-separated list of allowed origins. Falls back to
# the existing local-dev + Vercel origins if unset, so this is purely
# additive - no behavior change for the current deployment unless the
# env var is explicitly set.
_default_origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:5174",
    "http://127.0.0.1:5174",
    "https://ai-twin-frontend-flax.vercel.app",
]

_cors_env = os.getenv("CORS_ORIGINS", "").strip()

allowed_origins = (
    [origin.strip() for origin in _cors_env.split(",") if origin.strip()]
    if _cors_env
    else _default_origins
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# -----------------------------
# Startup
# -----------------------------

@app.on_event("startup")
def startup_event():
    initialize()

    # Security check: refuse to run silently on the insecure default
    # JWT signing secret. Warns loudly rather than crashing, so local
    # development without a .env still works - but makes it very hard
    # to accidentally ship this to production unnoticed.
    from backend.auth.security import SECRET_KEY
    if SECRET_KEY == "dev-only-insecure-secret-change-me":
        print(
            "\n"
            "==================== SECURITY WARNING ====================\n"
            "JWT_SECRET_KEY is not set - using the insecure development\n"
            "default. Every login token is forgeable by anyone who\n"
            "reads this source code. Set JWT_SECRET_KEY in your\n"
            "environment before deploying this anywhere but your own\n"
            "machine. See .env.example.\n"
            "============================================================\n"
        )

    rebuild_memory_index_from_db()
    load_memory_index()

    print("Memory FAISS rebuilt successfully.")


# -----------------------------
# Routers
# -----------------------------

app.include_router(notes_router)
app.include_router(upload_router)
app.include_router(conversations_router)
app.include_router(memory_router)
app.include_router(graph_router)
app.include_router(timeline_router)
app.include_router(profile_router)
app.include_router(documents_router)
app.include_router(search_router)
app.include_router(dashboard_router)
app.include_router(insights_router)
app.include_router(decision_router)
app.include_router(auth_router)


# -----------------------------
# Health / Home
# -----------------------------

@app.get("/")
def home():
    return {
        "message": "Welcome to AI Twin!"
    }


@app.get("/healthz")
def healthz():
    return {
        "status": "ok"
    }