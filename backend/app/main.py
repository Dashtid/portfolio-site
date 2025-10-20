"""
FastAPI main application
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.config import settings
from app.database import engine, Base
from app.api.v1 import companies, skills, projects, auth, github  # , analytics
from app.api import education
# Import models to ensure they're registered with Base
from app.models import company, skill, project, user, contact, education as education_model
from app.models import analytics as analytics_model

# Lifespan context manager for startup/shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("[OK] Database tables created/verified")
    yield
    # Shutdown
    await engine.dispose()
    print("[OK] Database connection closed")

# Create FastAPI instance
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Portfolio API with Vue.js frontend",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/v1")
app.include_router(companies.router, prefix="/api/v1")
app.include_router(skills.router, prefix="/api/v1")
app.include_router(projects.router, prefix="/api/v1")
app.include_router(education.router, prefix="/api/v1")
app.include_router(github.router, prefix="/api/v1/github", tags=["GitHub"])
# app.include_router(analytics.router, prefix="/api/v1/analytics", tags=["Analytics"])

# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "Portfolio API is running!",
        "version": settings.APP_VERSION,
        "docs": "/api/docs"
    }


# Health check endpoint
@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION
    }


# Test endpoint for frontend connection
@app.get("/api/v1/test")
async def test_endpoint():
    return {
        "status": "success",
        "message": "Hello from FastAPI!",
        "data": {
            "framework": "FastAPI",
            "version": settings.APP_VERSION,
            "description": "Your portfolio backend is ready!"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )