# Recipe Website

A full‑stack recipe website built with **FastAPI** (backend) and **React + Vite** (frontend).  
Everything you need to run, develop, test, and deploy in one place.

Tip: run the backend and frontend in separate terminals during development.

---

## Table of Contents
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Quick Start](#quick-start)
  - [Backend Setup](#backend-setup)
  - [Frontend Setup](#frontend-setup)
  - [Running Both Together](#running-both-together)
- [Environment Variables](#environment-variables)
- [API Endpoints](#api-endpoints)
- [Testing](#testing)
- [Docker](#docker)
- [Production Build](#production-build)
- [Contributing](#contributing)
- [License](#license)

---

## Tech Stack

**Backend**
- FastAPI
- Uvicorn (ASGI server)
- SQLAlchemy (ORM)
- Pydantic (data validation)
- (optional) PostgreSQL / SQLite

**Frontend**
- React 18+
- Vite (build tool)
- React Router (if used)
- Axios or Fetch (API calls)

---

## Project Structure

```
backend/    FastAPI app (API + admin panel), served on /api/*
frontend/   Vue 3 + Vite single page app
api/        Vercel serverless entrypoint that re-exports the FastAPI app
```

---

## Quick Start

Requires Node >= 22.12 (see `.nvmrc`) and Python >= 3.9.

### Backend Setup

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

The dev server proxies `/api` to `http://localhost:8000`, so the frontend calls
relative URLs and no CORS setup is needed. Open http://localhost:5173.

---

## Environment Variables

| Variable | Where | Default | Purpose |
| --- | --- | --- | --- |
| `DATABASE_URL` | backend / Vercel | `""` (uses local SQLite) | PostgreSQL connection string (required for durable data on Vercel) |
| `SUPABASE_URL` | backend / Vercel | `""` | Supabase project URL for persistent image uploads |
| `SUPABASE_SECRET_KEY` | backend / Vercel | `""` (uses local uploads) | Server-only Supabase secret key for Storage uploads |
| `SUPABASE_SERVICE_ROLE_KEY` | backend / Vercel | `""` | Legacy alternative to `SUPABASE_SECRET_KEY` |
| `SUPABASE_STORAGE_BUCKET` | backend / Vercel | `recipe-images` | Public Supabase Storage bucket for recipe images |
| `CLOUDINARY_URL` | backend / Vercel | `""` | Optional legacy Cloudinary upload fallback |
| `VITE_API_BASE_URL` | frontend build | `""` (same origin) | Point the frontend at a backend on a different origin |
| `ADMIN_USERNAME` / `ADMIN_PASSWORD` | backend | `admin` / `admin` | Basic auth for `/api/admin` |
| `SITE_BASE_URL` | backend | `""` (same origin) | Base URL the admin panel links to (e.g. `http://localhost:5173` in dev) |
| `RECIPE_DATA_DIR` | backend | `backend/data` | Where local SQLite database and uploads are stored |

---

## API Endpoints

| Method | Path | Description |
| --- | --- | --- |
| GET | `/api/recipes` | List recipes (`?q=` to search) |
| GET | `/api/recipes/{id}` | Single recipe |
| POST | `/api/recipes` | Create a recipe |
| DELETE | `/api/recipes/{id}` | Delete a recipe |
| GET | `/api/admin` | Admin panel (HTTP basic auth) |
| GET | `/api/media/{file}` | Uploaded images (local dev fallback) |

---

## Testing

```bash
cd backend && pytest
```

---

## Deploying to Vercel

`vercel.json` builds the frontend into `frontend/dist` and routes traffic:

- `/api/*` → the FastAPI app in `api/index.py` (Python serverless function)
- everything else → `index.html`, so client-side routes such as `/recipes/1` work

### Environment Variables on Vercel:
Add these in **Vercel Dashboard → Project Settings → Environment Variables**:
1. `DATABASE_URL`: Your PostgreSQL connection string from [Neon](https://neon.tech), [Supabase](https://supabase.com), or a Vercel Marketplace integration (e.g. `postgresql://user:password@ep-xyz.aws.neon.tech/neondb?sslmode=require`). Without it, Vercel falls back to temporary SQLite storage and recipes disappear when the function is recycled.
2. `ADMIN_USERNAME` & `ADMIN_PASSWORD`: Custom credentials for `/api/admin`.
3. For persistent image uploads, create a **public** Supabase Storage bucket named `recipe-images`, then add:
   - `SUPABASE_URL`: Project Settings → Data API → Project URL.
   - `SUPABASE_SECRET_KEY`: Project Settings → API Keys → Secret keys. Use a dedicated key for this backend.
   - Legacy projects can use `SUPABASE_SERVICE_ROLE_KEY` instead.
   - (Optional) `SUPABASE_STORAGE_BUCKET`: Use this only if the public bucket has a different name.

Keep Supabase secret and service role keys server-side. Never prefix them with `VITE_` or expose them to the frontend.
