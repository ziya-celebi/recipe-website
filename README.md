# Recipe Website

A full‑stack recipe website built with **FastAPI** (backend) and **React + Vite** (frontend).  
Everything you need to run, develop, test, and deploy in one place.

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
| `VITE_API_BASE_URL` | frontend build | `""` (same origin) | Point the frontend at a backend on a different origin |
| `ADMIN_USERNAME` / `ADMIN_PASSWORD` | backend | `admin` / `admin` | Basic auth for `/api/admin` |
| `SITE_BASE_URL` | backend | `""` (same origin) | Base URL the admin panel links to (e.g. `http://localhost:5173` in dev) |
| `RECIPE_DATA_DIR` | backend | `backend/data` | Where `recipes.json` and uploads are stored |

---

## API Endpoints

| Method | Path | Description |
| --- | --- | --- |
| GET | `/api/recipes` | List recipes (`?q=` to search) |
| GET | `/api/recipes/{id}` | Single recipe |
| POST | `/api/recipes` | Create a recipe |
| DELETE | `/api/recipes/{id}` | Delete a recipe |
| GET | `/api/admin` | Admin panel (HTTP basic auth) |
| GET | `/api/media/{file}` | Uploaded images |

---

## Testing

```bash
cd backend && pytest
```

---

## Deploying to Vercel

`vercel.json` builds the frontend to `frontend/dist` and routes traffic:

- `/api/*` → the FastAPI app in `api/index.py` (Python serverless function)
- everything else → `index.html`, so client-side routes such as `/recipes/1` work

Set `ADMIN_USERNAME` and `ADMIN_PASSWORD` in the Vercel project settings.

Note: serverless filesystems are ephemeral — recipes created through the admin
panel are written to `/tmp` and are lost when the instance recycles. Use a real
database or object storage for persistent content.
