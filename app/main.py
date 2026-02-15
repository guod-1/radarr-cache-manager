"""
Radarr Cache Manager - Main Application

A web-based tool for managing Radarr movie caching and Unraid mover exclusions
based on movie ratings.
"""

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from contextlib import asynccontextmanager
import logging
from pathlib import Path

from app.core.config import settings
from app.core.scheduler import scheduler
from app.routers import dashboard, settings as settings_router, movies, logs, operations

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(settings.log_file),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events"""
    # Startup
    logger.info("Starting Radarr Cache Manager...")
    logger.info(f"Config directory: {settings.config_dir}")
    logger.info(f"Scripts directory: {settings.scripts_dir}")
    
    # Start scheduler if enabled
    if settings.scheduler_enabled:
        scheduler.start()
        logger.info("Scheduler started")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Radarr Cache Manager...")
    if scheduler.running:
        scheduler.shutdown()
        logger.info("Scheduler stopped")

# Create FastAPI app
app = FastAPI(
    title="Radarr Cache Manager",
    description="Manage Radarr movie caching and Unraid mover exclusions",
    version="1.0.0",
    lifespan=lifespan
)

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Set up templates
templates = Jinja2Templates(directory="app/templates")

# Include routers
app.include_router(dashboard.router, tags=["dashboard"])
app.include_router(settings_router.router, prefix="/settings", tags=["settings"])
app.include_router(movies.router, prefix="/movies", tags=["movies"])
app.include_router(logs.router, prefix="/logs", tags=["logs"])
app.include_router(operations.router, prefix="/operations", tags=["operations"])

@app.get("/health")
async def health_check():
    """Health check endpoint for Docker"""
    return {"status": "healthy"}

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Redirect to dashboard"""
    return templates.TemplateResponse("dashboard.html", {"request": request})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5858)
