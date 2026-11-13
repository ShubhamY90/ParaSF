from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.db.engine import engine, Base
from app.api.auth import router as auth_router

# Create tables on startup (dev convenience; use Alembic for production)
Base.metadata.create_all(bind=engine)

app = FastAPI(title="ParaTrust API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)

@app.get("/api/health")
def health() -> dict:
    return {"status": "ok", "service": "paratrust-api", "stage": 1}
