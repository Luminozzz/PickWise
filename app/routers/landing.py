from fastapi import APIRouter, Depends
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.core.database import get_db

api_router = APIRouter()

@api_router.get("/", response_class=HTMLResponse)
async def landing_page():
    with open("app/templates/page.html") as f:
        return f.read()

@api_router.get("/api/v1/items")
async def get_items(db: AsyncSession = Depends(get_db)):
    result = await db.execute(text("SELECT * FROM mouse_model"))
    rows = result.mappings().all()
    return [dict(row) for row in rows]
