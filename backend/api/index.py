# Vercel serverless entrypoint for the FastAPI backend.
# Vercel's @vercel/python runtime detects the ASGI `app` object and serves it.
# vercel.json rewrites every request to this file, so FastAPI still sees the
# original path (e.g. /api/v1/items) and routes normally.
from app.main import app
