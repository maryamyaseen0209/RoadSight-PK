import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.app.api.v1.router import router as api_v1_router
from backend.app.core.config import settings
from backend.app.core.logging_config import logger
from backend.app.db.session import init_db, SessionLocal
from backend.app.services.model_loader import load_models_on_startup
from backend.app.services.experiment_sync import sync_experiments_to_database


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: ensure tables and storage directories exist
    logger.info("Initializing RoadSight-PK backend services...")
    init_db()
    settings.outputs_path
    settings.visualizations_path
    logger.info(f"Artifacts output directory mounted at: {settings.outputs_path}")
    logger.info(f"Visualizations directory mounted at: {settings.visualizations_path}")

    # Load defect detection models
    load_models_on_startup()

    # Automatically sync experiment metrics from CSV/JSON into SQLite
    db = SessionLocal()
    try:
        sync_experiments_to_database(db)
    finally:
        db.close()

    yield
    logger.info("RoadSight-PK backend services shutting down.")


app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Intelligent Pavement Defect Detection for Pakistani Roads & RDD2022",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static file mount for detected/annotated outputs, artifacts, and experiment visualizations
app.mount("/outputs", StaticFiles(directory=str(settings.outputs_path)), name="outputs")
app.mount("/uploads", StaticFiles(directory=str(settings.outputs_path)), name="uploads")
app.mount("/artifacts", StaticFiles(directory=str(settings.BASE_DIR / "artifacts")), name="artifacts")
app.mount("/visualizations", StaticFiles(directory=str(settings.visualizations_path)), name="visualizations")

# Include Versioned API Routes
app.include_router(api_v1_router, prefix=settings.API_V1_STR)


@app.get("/", tags=["Root"])
def root():
    return {
        "project": "RoadSight-PK API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": f"{settings.API_V1_STR}/health",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host=settings.HOST, port=settings.PORT, reload=True)
