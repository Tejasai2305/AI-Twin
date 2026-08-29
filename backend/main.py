from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.routers.conversations import router as conversations_router
from backend.routers.notes import router as notes_router
from backend.routers.memory import router as memory_router
from backend.documents.upload import router as upload_router

from backend.startup import initialize

from backend.services.memory_service import get_memories
from backend.embeddings.memory_vector_store import (
    build_memory_index,
    load_memory_index,
)


app = FastAPI()


# -----------------------------
# CORS
# -----------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
        "https://ai-twin-frontend-flax.vercel.app",
    ],
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

    build_memory_index(get_memories())
    load_memory_index()

    print("Memory FAISS rebuilt successfully.")


# -----------------------------
# Routers
# -----------------------------

app.include_router(notes_router)
app.include_router(upload_router)
app.include_router(conversations_router)
app.include_router(memory_router)


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