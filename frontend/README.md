# PickWise frontend

React + Vite catalogue UI for Lumino / PickWise.

## Run

```bash
cd Lumino/frontend
npm install
npm run dev
```

Open http://localhost:5173.

## Backend connection

The dev server proxies `/api/*` to the FastAPI backend so the browser uses one
origin. Start the backend first (from the repo root, the parent of `Lumino/`):

```bash
uvicorn Lumino.backend.app.main:app --reload
```

The catalogue calls `GET /api/v1/items`. If the backend runs somewhere other
than `http://localhost:8000`, set `VITE_API_TARGET` (see `.env.example`).

## Structure

- `src/api.js` — backend fetch wrapper
- `src/format.js` — turns raw `mouse_model` rows into card text/tags
- `src/components/` — `Navbar`, `Catalogue`, `ProductCard`, `ProductCardSkeleton`, `Logo`, `icons`
- `src/pages/LandingPage.jsx` — fetches items, shows skeletons while loading
- `src/index.css` — palette + all styles

## Notes

The card's description and the up/down (pro/con) lines are derived or
placeholdered — the backend `mouse_model` table has no `description`, `upside`,
or `downside` columns yet. `src/format.js` and `ProductCard.jsx` mark where real
data should plug in.