# Recipe Website

A small full-stack recipe site: a **FastAPI** backend (JSON API + server-rendered admin
panel) and a **Vue 3 + Vite** single-page frontend, deployed as one Vercel project.

- Browse and search recipes, open a recipe detail page, save favourites (stored in
  `localStorage`).
- Add and delete recipes — including image upload — from the admin panel at `/api/admin`.
- Recipes live in SQL (PostgreSQL when `DATABASE_URL` is set, otherwise local SQLite);
  images go to Supabase Storage when configured, otherwise to local disk.

## Table of Contents
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Quick Start](#quick-start)
- [Environment Variables](#environment-variables)
- [API Endpoints](#api-endpoints)
- [Admin Panel](#admin-panel)
- [Testing](#testing)
- [Docker](#docker)
- [Deploying to Vercel](#deploying-to-vercel)

## Tech Stack

**Backend** — FastAPI, Uvicorn, SQLAlchemy 2, Pydantic, Jinja2 (admin templates),
Mangum (Vercel ASGI adapter), psycopg2 (PostgreSQL).

**Frontend** — Vue 3 (`<script setup>` SFCs), Vue Router, Vite, plain `fetch` (`frontend/src/api.js`).

## Project Structure

```
backend/    FastAPI app: main.py (API), admin.py (admin panel), store.py (SQLAlchemy storage),
            models.py (Pydantic models), templates/, tests/, Dockerfile
frontend/   Vue 3 + Vite SPA: views/ (Home, Recipes, Recipe), components/, composables/
api/        Vercel serverless entrypoint that re-exports the FastAPI app
vercel.json Build + routing config for the single Vercel deployment
```

## Quick Start

Requires **Node >= 22.12** (see `.nvmrc`; Vite 8 fails on older Node) and **Python >= 3.11**
(the test suite imports `tomllib`).

Backend — API on http://localhost:8000:

```bash
python -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
cd backend && SITE_BASE_URL=http://localhost:5173 python -m uvicorn main:app --reload --port 8000
```

Frontend — SPA on http://localhost:5173:

```bash
cd frontend
npm install
npm run dev
```

`frontend/vite.config.js` proxies `/api`, `/api/media`, and `/api/static` to
`http://localhost:8000`, so the SPA only makes same-origin requests and no CORS setup is
needed. `SITE_BASE_URL` points the admin panel's "view site" links at the Vite dev server.

There are no seed recipes: a fresh database starts empty and shows the "No recipes yet"
state until you add recipes through the admin panel.

## Environment Variables

| Variable | Where | Default | Purpose |
| --- | --- | --- | --- |
| `DATABASE_URL` | backend / Vercel | `""` (local SQLite) | PostgreSQL connection string (required for durable data on Vercel). `POSTGRES_URL` / `POSTGRES_PRISMA_URL` also work |
| `SUPABASE_URL` | backend / Vercel | `""` | Supabase project URL for persistent image uploads |
| `SUPABASE_SECRET_KEY` | backend / Vercel | `""` (local uploads) | Server-only Supabase secret key for Storage uploads |
| `SUPABASE_SERVICE_ROLE_KEY` | backend / Vercel | `""` | Legacy alternative to `SUPABASE_SECRET_KEY` |
| `SUPABASE_STORAGE_BUCKET` | backend / Vercel | `recipe-images` | Public Supabase Storage bucket for recipe images |
| `CLOUDINARY_URL` | backend / Vercel | `""` | Optional legacy Cloudinary upload fallback |
| `VITE_API_BASE_URL` | frontend build | `""` (same origin) | Point the frontend at a backend on a different origin |
| `ADMIN_USERNAME` / `ADMIN_PASSWORD` | backend | `admin` / `admin` | Basic auth for `/api/admin` |
| `SITE_BASE_URL` | backend | `""` (same origin) | Base URL the admin panel links to (e.g. `http://localhost:5173` in dev) |
| `RECIPE_DATA_DIR` | backend | `backend/data` | Where the local SQLite database and uploads are stored (forced to `/tmp/recipe_data` on Vercel) |

Never expose Supabase secret or service-role keys to the frontend (no `VITE_` prefix).

## API Endpoints

| Method | Path | Description |
| --- | --- | --- |
| GET | `/` | Health/hello payload |
| GET | `/api/recipes` | List recipes (`?q=` searches title, description, ingredients) |
| GET | `/api/recipes/{id}` | Single recipe (404 if missing) |
| POST | `/api/recipes` | Create a recipe (JSON body: `title`, `description`, `image`, `ingredients[]`, `steps[]`) |
| DELETE | `/api/recipes/{id}` | Delete a recipe |
| GET | `/api/admin` | Admin panel (HTTP basic auth) |
| GET | `/api/media/{file}` | Uploaded images (local storage fallback) |

Interactive docs are available at `/docs` while the backend runs.

## Admin Panel

Open http://localhost:8000/api/admin and sign in with `ADMIN_USERNAME` / `ADMIN_PASSWORD`
(`admin` / `admin` by default). From there you can create a recipe with an uploaded image
and delete existing ones. The panel header shows the active storage backend
("PostgreSQL (Cloud)" vs "SQLite (Local)"), which is the quickest way to confirm database
wiring.

## Testing

```bash
cd backend && ../.venv/bin/python -m pytest
```

`backend/tests/test_main.py` covers the API and admin flows; `test_deployment.py` checks the
Vercel/deployment configuration. CI (`.github/workflows/ci.yml`) runs the backend tests, a
Docker image smoke test, and a frontend build on every push and pull request.

## Docker

The backend ships a Dockerfile:

```bash
docker build -t recipe-backend backend
docker run -d -p 8000:8000 --name recipe-backend recipe-backend
curl --fail http://localhost:8000/api/recipes
```

## Deploying to Vercel

`vercel.json` builds the frontend into `frontend/dist` and routes traffic:

- `/api/*` → the FastAPI app in `api/index.py` (Python serverless function)
- everything else → `index.html`, so client-side routes such as `/recipes/1` work

Set these in **Vercel Dashboard → Project Settings → Environment Variables**:

1. `DATABASE_URL` — PostgreSQL connection string from [Neon](https://neon.tech),
   [Supabase](https://supabase.com), or a Vercel Marketplace integration, e.g.
   `postgresql://user:password@ep-xyz.aws.neon.tech/neondb?sslmode=require`. Without it the
   function falls back to SQLite under `/tmp` and recipes disappear when it is recycled.
2. `ADMIN_USERNAME` / `ADMIN_PASSWORD` — credentials for `/api/admin`.
3. For persistent image uploads, create a **public** Supabase Storage bucket named
   `recipe-images` and set `SUPABASE_URL` (Project Settings → Data API) and
   `SUPABASE_SECRET_KEY` (Project Settings → API Keys). Older projects can use
   `SUPABASE_SERVICE_ROLE_KEY`; set `SUPABASE_STORAGE_BUCKET` only if the bucket has a
   different name. Without Supabase, uploads land in the function's ephemeral `/tmp`.
