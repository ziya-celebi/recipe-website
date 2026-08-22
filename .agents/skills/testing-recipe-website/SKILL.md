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
- Recipe data: `backend/data/recipes.json`, uploads in `backend/data/uploads`; override
  the location with `RECIPE_DATA_DIR=/tmp/recipe_data_clean` (the store creates the dir).
- `store.py` seeds `SEED_RECIPES` only when the JSON file does not exist. As of the
  "remove seed recipes" change `SEED_RECIPES` is empty, so a fresh dir starts at zero
  recipes and ids restart at 1. **A stale `backend/data/recipes.json` from an older
  checkout still holds the old 6 seeds** — always point `RECIPE_DATA_DIR` at a fresh
  directory (or delete the JSON) when testing empty-state / seeding behaviour.
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
everything else (a working helper was kept at `/home/ubuntu/vercel_sim.py`):

```bash
cd frontend && npm run build
cd .. && .venv/bin/python -m uvicorn vercel_sim:app --port 8080
```

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
- `/api/media/*` is a Starlette `StaticFiles` mount inside the function; it only works if
  Vercel's `/api/(.*)` rewrite preserves the original path to the function. Verify by
  uploading an image on a preview deployment.

## Devin Secrets Needed

None — local admin credentials default to `admin`/`admin`.
