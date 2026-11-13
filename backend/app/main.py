from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.db.engine import engine, Base

# Import all models so Base.metadata knows about every table
from app.models import user  # noqa: F401
from app.models import stage2  # noqa: F401
from app.models import simulation  # noqa: F401
from app.models import sensor  # noqa: F401

# Import routers
from app.api.auth import router as auth_router
from app.api.farmers import router as farmers_router
from app.api.policies import router as policies_router, admin_router
from app.api.geo import router as geo_router
from app.api.simulation import router as simulation_router
from app.api.sensors import router as sensors_router

# Create tables on startup (dev convenience; use Alembic for production)
Base.metadata.create_all(bind=engine)

app = FastAPI(title="ParaTrust API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(farmers_router)
app.include_router(policies_router)
app.include_router(admin_router)
app.include_router(geo_router)
app.include_router(simulation_router)
app.include_router(sensors_router)

@app.get("/api/health")
def health() -> dict:
    return {"status": "ok", "service": "paratrust-api", "stage": 5}
