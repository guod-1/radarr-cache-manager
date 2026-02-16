import logging
import os
from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse

from app.core.scheduler import SchedulerService
from app.routers import dashboard, movies, shows, exclusions, settings, logs, stats, operations
from app.core.config import get_user_settings

# Configure logging to both console and file
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.FileHandler("/config/app.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

app = FastAPI(title="Mover Tuning Exclusion Manager")

app.include_router(dashboard.router)
app.include_router(movies.router, prefix="/movies", tags=["movies"])
app.include_router(shows.router, prefix="/shows", tags=["shows"])
app.include_router(exclusions.router, prefix="/exclusions", tags=["exclusions"])
app.include_router(settings.router, prefix="/settings", tags=["settings"])
app.include_router(logs.router, prefix="/logs", tags=["logs"])
app.include_router(stats.router, prefix="/stats", tags=["stats"])
app.include_router(operations.router, prefix="/operations", tags=["operations"])

@app.on_event("startup")
async def startup_event():
    logger.info("Starting Mover Tuning Exclusion Manager...")
    scheduler = SchedulerService()
    scheduler.start()

@app.exception_handler(404)
async def custom_404_handler(request: Request, exc):
    return RedirectResponse("/")
