# Deploying AI-Twin

The app is provider-neutral: the backend is a standard FastAPI app
(`uvicorn backend.main:app`) that works on any platform that can run
a Python web process, and automatically switches between SQLite
(local dev) and PostgreSQL (production) based on whether `DATABASE_URL`
is set - see `backend/database/config.py` and `backend/database/pg_compat.py`.

This doc gives one concrete path (Render + Vercel) since a worked
example is more useful than an abstract one, plus notes on adapting
it to Railway, Fly.io, or anywhere else.

## Architecture recap

- **Backend**: FastAPI, `backend/main.py`. Reads/writes SQLite by
  default, or PostgreSQL if `DATABASE_URL` is set.
- **Frontend**: React + Vite, `frontend/`. A static build (`npm run
  build`) that talks to the backend over HTTP, configured via
  `VITE_API_BASE_URL`.
- **Local data**: uploaded PDFs, the FAISS memory index, and the
  FAISS PDF index all live under `AI_TWIN_DATA_DIR` (defaults to the
  project root). In production this needs to be either a persistent
  disk or accepted as ephemeral (see "Persistent storage" below).

## 1. Backend

### Environment variables

Copy `.env.example` to `.env` locally, or set these in your platform's
dashboard for production. See that file for the full list and
descriptions; the ones that matter most for going to production:

| Variable | Required in production | Notes |
|---|---|---|
| `GEMINI_API_KEY` | Yes | AI model access |
| `TAVILY_API_KEY` | Yes (if using web search) | |
| `JWT_SECRET_KEY` | **Yes** | App boots without it but prints a loud warning and uses an insecure default - never leave unset in production |
| `DATABASE_URL` | Recommended | Omit for SQLite (fine for small/single-instance deployments); set to a `postgresql://...` URL for production |
| `CORS_ORIGINS` | Yes | Comma-separated list of your frontend's real origin(s) |
| `AI_TWIN_DATA_DIR` | Recommended | Where uploads/FAISS indexes are stored - see below |

### Deploying to Render (concrete example)

A ready-to-use `render.yaml` blueprint is included at the repo root.

1. Push this repo to GitHub/GitLab.
2. In Render, choose **New > Blueprint** and point it at the repo -
   it will read `render.yaml` and create the web service + a
   PostgreSQL database automatically.
3. Set the `sync: false` env vars in the Render dashboard
   (`GEMINI_API_KEY`, `TAVILY_API_KEY`, `CORS_ORIGINS`) - these are
   marked `sync: false` deliberately so real secrets never live in
   the repo.
4. Render provides the health check at `/healthz` (already wired up
   in `render.yaml`).

If deploying manually instead of via Blueprint:
- **Build command**: `pip install -r requirements.txt`
- **Start command**: `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`
- **Health check path**: `/healthz`

### Deploying to Railway / Fly.io / any other platform

The included root-level `Procfile` (`web: uvicorn backend.main:app
--host 0.0.0.0 --port $PORT`) is the standard format Railway and
similar Heroku-style platforms auto-detect. Fly.io needs a
`fly launch` + the same start command in `fly.toml`. In every case:
set the same environment variables listed above, and provision a
PostgreSQL database if you want production-grade persistence (add-on
or managed service - set its connection string as `DATABASE_URL`).

### Persistent storage (important)

`AI_TWIN_DATA_DIR` holds three things: the SQLite file (irrelevant if
using `DATABASE_URL`/Postgres), uploaded PDF files, and the FAISS
indexes for memory + PDF search.

- **Memories self-heal on restart**: `rebuild_memory_index_from_db()`
  runs at startup and rebuilds the memory FAISS index from the
  database every time, so memory search survives a redeploy even on
  ephemeral disk.
- **Uploaded PDFs and their extracted text do NOT self-heal**: the
  actual PDF file and its indexed chunks live only on disk
  (`AI_TWIN_DATA_DIR/uploads/` and the PDF FAISS index), not in the
  database. On ephemeral storage, a redeploy will make previously
  uploaded documents show up in the Document Center as "file missing
  on disk" (the Insights page will flag this automatically) and no
  longer searchable.
- **To fix**: mount a persistent volume/disk at whatever path you set
  `AI_TWIN_DATA_DIR` to (Render: a paid Disk; Railway: a Volume;
  Fly.io: a Volume). Without one, treat uploaded documents as
  session-scoped rather than permanent.

## 2. Frontend (Vercel)

1. Copy `frontend/.env.example` to `frontend/.env` locally, or set
   `VITE_API_BASE_URL` in Vercel's dashboard to your deployed
   backend's URL (e.g. `https://ai-twin-backend.onrender.com`).
2. In Vercel: **New Project**, import this repo, and set the
   **Root Directory** to `frontend` (this is a monorepo - the
   backend lives at the repo root, so Vercel needs to be told where
   the frontend actually is).
3. Vercel auto-detects Vite: build command `npm run build`, output
   directory `dist`. No extra config needed beyond the root
   directory and the env var above.
4. After deploying, set the frontend's real Vercel URL as one of the
   values in the backend's `CORS_ORIGINS`.

## 3. First-run checklist

- [ ] Backend `/healthz` returns `{"status": "ok"}`
- [ ] No "SECURITY WARNING" about `JWT_SECRET_KEY` in the backend logs
- [ ] Frontend can sign up / log in (confirms `VITE_API_BASE_URL` and
      `CORS_ORIGINS` are both correct)
- [ ] A test chat message gets a response (confirms `GEMINI_API_KEY`)
- [ ] Uploading a PDF and asking about it works (confirms
      `AI_TWIN_DATA_DIR` is writable)
- [ ] Run the test suite against the deployed config before going
      live: `pytest backend/tests/` (see `pytest.ini`)
