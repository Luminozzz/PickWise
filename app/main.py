from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import landing

app = FastAPI(
    title="Pickwise",
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

app.include_router(landing.api_router)
