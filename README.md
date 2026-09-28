# AI-Twin

A personal AI Twin — a persistent digital representation of you, built on a
long-term memory system, document intelligence, and a growing set of pages
(profile, knowledge graph, timeline, dashboard, insights, decision support)
that all read from the same underlying memory rather than duplicating it.

The AI Twin remembers what you tell it (and what your documents say),
classifies it, tracks when facts change over time, and answers questions
about you with real, traceable sources — never invented ones.

## Features

**Chat**
- Multi-conversation chat with Gemini, streaming responses, stop generation,
  edit message, regenerate response, per-conversation PDF attachments

**Memory**
- Long-term memory with confidence scores, source attribution, and 11
  semantic types (education, career, technical skill, project, etc.)
- Contradiction detection: when a new fact conflicts with an old one (e.g.
  an updated CGPA), the old value is preserved with a timestamp rather than
  silently overwritten
- Full temporal history per fact — see exactly what changed and when
- Memory Center UI: search, filter, edit, deactivate/reactivate, view history

**Document intelligence**
- PDF upload, text extraction, chunking, and FAISS-backed semantic search
- Documents are isolated per conversation during chat (a document in one
  conversation never leaks into another's context)
- Document Center: view indexing status, chunk counts, delete documents
  (which also cleans up their search index — no stale/ghost results)

**Knowledge Graph & Timeline**
- Personal knowledge graph (You → category → fact) built live from memory
- Chronological timeline merging conversations, documents, and memory
  changes into one feed

**AI Twin Profile**
- Auto-built profile from verified memories, organized into sections
  (About, Education, Career, Skills, Projects, ...). Honestly reports what
  it doesn't know yet instead of guessing

**Search, Dashboard, Insights**
- Global search across conversations, memories, and documents at once
- Dashboard summarizing everything (counts, graph/profile summaries, recent
  activity)
- Insights: flags duplicate memories, low-confidence facts, recent
  contradictions, profile gaps, and unindexed/missing documents —
  suggestions only, nothing is changed automatically

**Decision Support**
- Compare options against criteria you supply, with scores, trade-offs, and
  explicit assumptions — never guesses at your personal preferences

**Accounts**
- Optional authentication (signup/login/JWT sessions). The app works
  perfectly well with no account at all (single-user/local mode); once
  someone signs in, all of the above is scoped to their account only

## Architecture

```
AI-Twin/
├── backend/
│   ├── main.py                 FastAPI app, router registration, CORS, startup
│   ├── auth/                   Password hashing, JWT, optional-auth dependency
│   ├── database/                SQLite by default, Postgres via DATABASE_URL
│   │                            (backend/database/pg_compat.py is the compat shim)
│   ├── routers/                 One file per feature area (memory, graph,
│   │                            timeline, profile, documents, search,
│   │                            dashboard, insights, decision, auth, notes,
│   │                            conversations)
│   ├── services/                Business logic behind each router
│   │   └── pipeline/            The chat pipeline: tool → memory → history
│   │                            → retrieval → prompt → LLM stages
│   ├── ai/                      Gemini client, memory extraction prompt
│   ├── agent/                   Tool routing (calculator, web search)
│   ├── documents/                PDF upload, extraction, chunking, FAISS index
│   ├── embeddings/               Memory embedding + FAISS index
│   └── tests/                   pytest suite (see Testing below)
│
├── frontend/
│   └── src/
│       ├── components/           One panel per page (Chat, Memory, Graph,
│       │                        Timeline, Profile, Documents, Search,
│       │                        Dashboard, Insights, Decision Support)
│       └── services/             One API client per feature, all routed
│                                 through httpClient.js (shared axios
│                                 instance + auth token handling)
│
├── requirements.txt
├── Procfile / render.yaml        Deployment (see DEPLOYMENT.md)
├── .env.example
└── pytest.ini
```

## Technology stack

**Backend**: Python, FastAPI, Uvicorn, SQLite/PostgreSQL, FAISS, NumPy,
PyMuPDF, Gemini (`google-genai`), Tavily (web search), Pydantic, bcrypt,
PyJWT

**Frontend**: React, Vite

## Installation

### Prerequisites
- Python 3.10+
- Node.js 18+
- A Gemini API key ([ai.google.dev](https://ai.google.dev)) and, optionally,
  a Tavily API key for web search

### Backend setup

```bash
cd AI-Twin
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env            # then fill in GEMINI_API_KEY, TAVILY_API_KEY
```

### Frontend setup

```bash
cd frontend
npm install
cp .env.example .env            # defaults to http://127.0.0.1:8000, fine for local dev
```

## Environment variables

See `.env.example` (backend) and `frontend/.env.example` (frontend) for the
full, current list with descriptions. The short version:

| Variable | Where | Required |
|---|---|---|
| `GEMINI_API_KEY` | backend | Yes |
| `TAVILY_API_KEY` | backend | Only if using web search |
| `JWT_SECRET_KEY` | backend | Required in production (see Security below) |
| `DATABASE_URL` | backend | No — omit for local SQLite |
| `CORS_ORIGINS` | backend | Required in production |
| `AI_TWIN_DATA_DIR` | backend | No — defaults to the project root |
| `VITE_API_BASE_URL` | frontend | No — defaults to `http://127.0.0.1:8000` |

## Running locally

```bash
# Terminal 1 — backend
uvicorn backend.main:app --reload

# Terminal 2 — frontend
cd frontend && npm run dev
```

The backend runs at `http://127.0.0.1:8000` (health check: `/healthz`), the
frontend at `http://localhost:5173`.

## Database setup

No setup needed for local development — a SQLite file (`notes.db`) is
created automatically in `AI_TWIN_DATA_DIR` on first run, including all
migrations for tables added over the project's development (memory
metadata, temporal fields, user accounts, etc.).

For production, set `DATABASE_URL` to a PostgreSQL connection string; the
app detects this automatically and switches drivers (see
`backend/database/config.py`). No code changes needed either way — see
`backend/database/pg_compat.py` for how the same SQL works against both.

## AI model setup

The app uses Google's Gemini via the `google-genai` SDK
(`backend/ai/gemini_service.py`) for chat responses, memory extraction and
classification, contradiction detection, title generation, tool routing,
and decision support scoring. Get a key at
[ai.google.dev](https://ai.google.dev) and set `GEMINI_API_KEY`.

## PDF / RAG setup

No separate setup step — PDF upload, extraction (PyMuPDF), chunking, and
FAISS indexing are all built in. Upload a PDF from within a chat
conversation; it's indexed immediately and scoped to that conversation
(document isolation — a PDF uploaded in one conversation is never used to
answer questions in another). Manage all uploaded documents from the
Document Center page.

## Testing

```bash
pytest backend/tests/
```

73 tests covering auth, conversations, memory (including contradiction
detection and temporal chains), documents (including upload security and
stale-index prevention), graph/timeline/profile, global search, dashboard,
insights, decision support, and — throughout all of the above — cross-user
data isolation. See `pytest.ini` for scope notes (a few ad-hoc, non-pytest
debug scripts under `tests/` predate this suite and are intentionally
excluded from discovery).

## Production build

```bash
cd frontend
npm run build      # outputs to frontend/dist/
```

The backend needs no build step — deploy the source directly and run it
with `uvicorn backend.main:app`.

## Deployment

See [`DEPLOYMENT.md`](./DEPLOYMENT.md) for a full guide (Render + Vercel
worked example, plus notes for Railway/Fly.io), including a real,
important note about persistent storage for uploaded documents.

## Security

- Passwords hashed with bcrypt; sessions are signed JWTs
- Every memory, conversation, and document is scoped to its owning user;
  extensively tested for cross-user isolation (see `backend/tests/`)
- Parameterized SQL everywhere — no string-built queries
- Uploaded filenames are sanitized (path traversal stripped) and
  namespaced on disk to prevent collisions; uploads are size-limited
- Retrieved document/web content is explicitly framed to the model as
  data, not instructions (prompt injection defense)
- The app prints a loud startup warning if `JWT_SECRET_KEY` is left unset
  in a way that looks like production
- See `DEPLOYMENT.md`'s security notes and `.env.example` for what must be
  configured before going live

## Future improvements

- Enforce authentication on write endpoints rather than allowing an
  unauthenticated/legacy mode (currently supported deliberately, so the
  app works standalone without requiring an account)
- Multimodal support (images, scanned/OCR'd PDFs, audio) — the current
  architecture (isolated retrieval per source type) is designed to extend
  to new source types without reworking existing ones
- Structured document extraction (entities, dates, skills) beyond plain
  text chunking
- Export (JSON/CSV) of profile, memories, conversations, and graph data
- CI (run `pytest backend/tests/` automatically on push)
