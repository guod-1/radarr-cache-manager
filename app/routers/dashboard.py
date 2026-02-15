from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from app.services.radarr import get_radarr_client
from app.services.sonarr import get_sonarr_client
from app.services.exclusions import get_exclusion_manager
from app.core.scheduler import get_scheduler
import logging

logger = logging.getLogger(__name__)
router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Dashboard home page"""
    
    # 1. Check Radarr
    radarr_connected = False
    try:
        radarr_connected = get_radarr_client().test_connection()
    except Exception:
        pass

    # 2. Check Sonarr
    sonarr_connected = False
    try:
        sonarr_connected = get_sonarr_client().test_connection()
    except Exception:
        pass

    # 3. Get Exclusion Stats
    exclusion_manager = get_exclusion_manager()
    exclusion_stats = exclusion_manager.get_exclusion_stats()
    
    # 4. Compile Stats for Template
    # We use .get('total_count', 0) to be safe even if the key is missing
    stats = {
        "radarr_connected": radarr_connected,
        "sonarr_connected": sonarr_connected,
        "exclusion_count": exclusion_stats.get('total_count', 0),
        "file_size": exclusion_stats.get('file_size', 0)
    }

    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "stats": stats
    })
