import logging
import os
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse

from app.core.config import get_user_settings
from app.core.scheduler import get_scheduler
from app.routers import dashboard, settings, movies, shows, logs, operations, exclusions, stats

# Initialize Logging to File
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("/config/app.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Mover Tuning Exclusion Manager")
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Include all routers
app.include_router(dashboard.router, tags=["Dashboard"])
app.include_router(exclusions, stats.router, prefix="/exclusions", tags=["Exclusions"])
app.include_router(movies.router, prefix="/movies", tags=["Movies"])
app.include_router(shows.router, prefix="/shows", tags=["Shows"])
app.include_router(settings.router, prefix="/settings", tags=["Settings"])
app.include_router(logs.router, prefix="/logs", tags=["Logs"])
app.include_router(operations.router, prefix="/operations", tags=["Operations"])

@app.on_event("startup")
async def startup_event():
    logger.info("Starting Mover Tuning Exclusion Manager...")
    try:
        scheduler = get_scheduler()
        scheduler.start()
        logger.info("Scheduler service initialized.")
    except Exception as e:
        logger.error(f"Scheduler failed to start: {e}")

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.exception_handler(404)
async def custom_404_handler(request: Request, exc):
    return RedirectResponse(url="/")
