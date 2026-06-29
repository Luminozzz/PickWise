from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import landing, recommend, profile
from database.models import init_db

app = FastAPI(
    title="Lumino",
    description="Helping users to pick the best product based on their preferences",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    redirect_slashes=False,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def _ensure_tables():
    init_db()


app.include_router(landing.api_router)
app.include_router(recommend.api_router)
app.include_router(profile.api_router)
