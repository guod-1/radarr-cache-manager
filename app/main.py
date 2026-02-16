import logging
import os
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse

from app.core.scheduler import SchedulerService
from app.routers import dashboard, movies, shows, exclusions, settings, logs, stats, operations
from app.core.config import get_user_settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

logger = logging.getLogger(__name__)

app = FastAPI(title="Mover Tuning Exclusion Manager")

# Mount static files (if you had them, currently using CDN)
# app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Include Routers
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
    
    # 1. Initialize Scheduler
    scheduler = SchedulerService()
    scheduler.start()
    logger.info("Scheduler service initialized.")
    
    # 2. Ensure Log Directory Exists
    try:
        settings = get_user_settings()
        log_path = settings.exclusions.ca_mover_log_path
        # Only try to create if it looks like a file path (has an extension)
        if "." in os.path.basename(log_path):
            log_dir = os.path.dirname(log_path)
            if log_dir and not os.path.exists(log_dir):
                os.makedirs(log_dir, exist_ok=True)
                logger.info(f"Created log directory: {log_dir}")
                
                # Create empty file if it doesn't exist so we don't crash reading it
                if not os.path.exists(log_path):
                    with open(log_path, 'w') as f:
                        f.write("")
                    logger.info(f"Created empty log file: {log_path}")
    except Exception as e:
        logger.error(f"Failed to initialize log directory: {e}")

@app.exception_handler(404)
async def custom_404_handler(request: Request, exc):
    return RedirectResponse("/")
