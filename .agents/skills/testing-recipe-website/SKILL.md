---
name: testing-recipe-website
description: How to run and end-to-end test the recipe-website app locally (FastAPI backend, Vue 3 + Vite frontend, Vercel-style prod simulation).
---

# Testing the recipe-website app locally

## Services

Backend (FastAPI, port 8000). Python venv with deps lives at `.venv` in the repo root:

```bash
cd backend && SITE_BASE_URL=http://localhost:5173 ../.venv/bin/python -m uvicorn main:app --port 8000
```

- `SITE_BASE_URL` drives the admin panel's "Open Public Site" / "View" links. Leave it
  empty for same-origin (production) behaviour; set it to the Vite dev URL in dev.
- Storage is SQLAlchemy-backed (`backend/store.py`). `get_db_url()` prefers
  `DATABASE_URL` / `POSTGRES_URL` / `POSTGRES_PRISMA_URL` (rewriting `postgres://` to
  `postgresql://`) and otherwise falls back to SQLite at `<data_dir>/recipes.db`.
  The admin panel header shows which one is active: "PostgreSQL (Cloud)" vs
  "SQLite (Local)" — a fast, visual way to confirm DB wiring.
- Data dir: `backend/data` (uploads in `backend/data/uploads`); override with
  `RECIPE_DATA_DIR=/tmp/recipe_data_clean`. **`api/index.py` hard-sets
  `RECIPE_DATA_DIR=/tmp/recipe_data`**, so in the prod-sim `RECIPE_DATA_DIR` from the
  environment is ignored — delete `/tmp/recipe_data` to get a clean SQLite state.
- `SEED_RECIPES` is empty, so a fresh DB starts at zero recipes and ids restart at 1.
  A legacy `backend/data/recipes.json` is migrated into the DB on first init, and a stale
  `recipes.db`/`recipes.json` from an older checkout keeps old rows — delete them (both are
  gitignored) when testing empty-state behaviour.
- Testing durable storage without cloud credentials: run a throwaway Postgres in Docker
  and point `DATABASE_URL` at it, e.g.
  `docker run -d --name pgtest -e POSTGRES_PASSWORD=pgpass -e POSTGRES_DB=recipes -p 5433:5432 postgres:16-alpine`
  then `DATABASE_URL=postgresql://postgres:pgpass@127.0.0.1:5433/recipes`. Restarting the
  app process and re-checking `/api/recipes` proves persistence; restarting *without*
  `DATABASE_URL` (SQLite fallback, empty catalogue) is a good adversarial control.
- Empty catalogue should render the "No recipes yet" empty state on both Home and
  `/recipes`; the "No recipes found … matching \"…\"" block is the *search* empty state
  and appearing on an empty catalogue would be a regression (branch ordering in
  `RecipesPage.vue`).

Frontend (Vite dev server, port 5173) — **requires Node >= 22.12**; Vite 8 crashes on
Node 20 with a missing rolldown native binding:

```bash
export NVM_DIR="$HOME/.nvm"; . "$NVM_DIR/nvm.sh"; nvm use 22.12.0
cd frontend && npm install && npm run dev
```

`vite.config.js` proxies `/api`, `/api/media`, `/api/static` to `http://localhost:8000`,
and `frontend/src/api.js` uses a relative API base (override with `VITE_API_BASE_URL`),
so all app requests should be same-origin. If you see cross-origin requests to
`localhost:8000` from the SPA, the relative-base wiring is broken.

## Simulating the Vercel production deployment

`vercel.json` deploys the built SPA plus a Python function at `api/index.py` with
rewrites `/api/(.*) -> /api/index` and `/(.*) -> /index.html`. To reproduce that locally,
build the frontend and serve `frontend/dist` with an ASGI app that routes `/api*` to
`backend/main.py:app`, serves existing dist files, and falls back to `index.html` for
everything else. A working helper is kept at `/home/ubuntu/vercel_sim.py` (recreate it if
the box was reset — it importing `api.index` also exercises the real function entrypoint):

```bash
cd frontend && npm run build           # needs node 22.12 (nvm use 22.12.0)
cd /home/ubuntu && DATABASE_URL=... /home/ubuntu/repos/recipe-website/.venv/bin/python \
  -m uvicorn vercel_sim:app --port 8080   # run from the dir containing vercel_sim.py
```

Pitfalls seen:
- Do **not** `Mount("/api", api_app)` — Starlette strips the prefix while the FastAPI
  routes already include `/api`, giving 404s on `/api/recipes` and `/api/admin`. Dispatch
  with a plain ASGI callable that forwards `/api*` paths unchanged.
- Start long-running servers in a persistent background shell; `nohup ... &` from a
  one-shot shell gets killed with the shell, and a stale process still holding :8080 makes
  a "restarted" server silently fail to bind. `vercel_sim.py` is not in the repo, so a
  reset box needs it recreated; check for a stale uvicorn first with
  `ss -lptn 'sport = :8000'` (and `:8080`) and `kill -9` it.

Then check `/`, a deep link like `/recipes/1`, `/api/recipes`, and `/api/admin`.

## Admin panel

- URL: `http://localhost:8000/api/admin` (prod-sim: `http://127.0.0.1:8080/api/admin`).
- HTTP basic auth, defaults `admin` / `admin` (`ADMIN_USERNAME` / `ADMIN_PASSWORD`).
- In Chrome you can pass credentials inline (`http://admin:admin@host/api/admin`), but
  note this makes the SPA's `history.replaceState` throw a `SecurityError` if you then
  navigate into the Vue app from that tab — prefer typing credentials in the auth dialog
  when you will click through to the public site.
- Uploading an image: click "Choose File", then in the GTK file dialog press `ctrl+l`
  and type the absolute path. Uploaded images get URLs under `/api/media/<uuid>.<ext>`.
  PIL is not installed in `.venv`; generate test images with ImageMagick, e.g.
  `convert -size 800x500 xc:'#dc285a' /tmp/test.png`.
- `/api/media/{filename}` is GET-only, so `curl -I` reports 405. Inspect media responses
  with `curl -s -D - -o /dev/null <url>` instead.
- Delete uses a JS `confirm()` dialog; accept it, then the app 303-redirects to
  `/api/admin?deleted=1`. The recipe row shifts up after a page reload — re-screenshot
  before clicking the 🗑️ button so you hit the right row.

## Favorites

- Stored in `localStorage` under `recipe_website_favorites`; clear it between runs
  (`localStorage.removeItem('recipe_website_favorites')`) or counts leak across tests.
- Known quirk: the "❤️ Saved (N)" count is taken straight from localStorage and is not
  reconciled against recipes that were deleted server-side, so it can read `1` while the
  list correctly renders no cards. Cosmetic, pre-existing.

## Things that may still break on real Vercel

- Uploaded images and created/deleted recipes are written under `/tmp` on Vercel
  (`api/index.py` sets `RECIPE_DATA_DIR=/tmp/recipe_data`), so they are ephemeral and not
  shared across function instances. With seeds removed, a cold start now yields an
  **empty** catalogue (the "No recipes yet" state) rather than falling back to demo
  recipes — expect admin-created content to vanish on real Vercel unless durable storage
  is added.
- Uploaded images are no longer written to disk: `/api/media/{filename}` is a route that
  serves bytes from the `recipe_images` table (falling back to legacy files in
  `uploads_dir()`), so images are durable whenever `DATABASE_URL` points at PostgreSQL.
  Recipes created before that change still reference files lost from `/tmp`.

## Python version gotcha for the test suite

`backend/tests/test_deployment.py` imports `tomllib` (stdlib only on **Python 3.11+**),
but `pyproject.toml` declares `requires-python >=3.9` and the default box venv may be
Python 3.10 — there `pytest` aborts during collection with
`ModuleNotFoundError: No module named 'tomllib'`. Create the venv with
`~/.pyenv/versions/3.11.11/bin/python -m venv ...` (or use `tomli` as a fallback) when
running the full suite.

## Devin Secrets Needed

None — local admin credentials default to `admin`/`admin`.
