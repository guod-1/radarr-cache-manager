from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from app.services.radarr import get_radarr_client
from app.services.sonarr import get_sonarr_client
from app.services.exclusions import get_exclusion_manager
from app.services.ca_mover import get_ca_mover_monitor
from app.core.config import get_user_settings
from app.core.scheduler import get_scheduler
import logging

logger = logging.getLogger(__name__)
router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Dashboard home page"""
    
    user_settings = get_user_settings()
    
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
    
    # 4. Get CA Mover Stats
    ca_monitor = get_ca_mover_monitor()
    ca_stats = ca_monitor.parse_log()

    # 5. Get Scheduler Stats
    scheduler = get_scheduler()
    
    # 6. Prepare Context
    # We unpack these directly so the template can find {{ radarr_connected }}
    context = {
        "request": request,
        "radarr_connected": radarr_connected,
        "radarr_url": user_settings.radarr.url,
        "sonarr_connected": sonarr_connected,
        "sonarr_url": user_settings.sonarr.url,
        "scheduler_enabled": scheduler.running,
        "next_run": scheduler.get_next_run_time(),
        
        "exclusion_count": exclusion_stats.get('total_count', 0),
        "exclusion_files": exclusion_stats.get('total_count', 0), 
        "exclusion_dirs": 0,
        
        "ca_mover_status": ca_stats.get('status', 'no_logs'),
        "ca_mover_excluded": ca_stats.get('files_excluded', 0),
        
        "tag_search_id": user_settings.radarr_tag_operation.search_tag_id,
        "tag_replace_id": user_settings.radarr_tag_operation.replace_tag_id,
        "custom_folder_count": len(user_settings.exclusions.custom_folders),
        "exclude_tag_count": len(user_settings.exclusions.exclude_tag_ids),
    }

    return templates.TemplateResponse("dashboard.html", context)
