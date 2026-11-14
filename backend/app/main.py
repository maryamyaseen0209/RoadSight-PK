from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.app.api.v1.router import router as api_v1_router
from backend.app.core.config import settings
from backend.app.core.logging_config import logger
from backend.app.db.session import init_db


# Ensure DB tables are created upon import as well as on lifespan startup
init_db()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: ensure tables and storage directories exist
    logger.info("Initializing RoadSight-PK backend services...")
    init_db()
    settings.outputs_path
    logger.info(f"Artifacts output directory mounted at: {settings.outputs_path}")
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

# Static file mount for detected/annotated outputs
app.mount("/outputs", StaticFiles(directory=str(settings.outputs_path)), name="outputs")

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
