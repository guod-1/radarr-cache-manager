from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from app.services.ca_mover import get_mover_parser
from app.services.exclusions import get_exclusion_manager
from app.services.radarr import get_radarr_client
from app.services.sonarr import get_sonarr_client
import datetime
import os

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

def format_filesize(value):
    if not value: return "0 B"
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if value < 1024.0:
            return f"{value:3.1f} {unit}"
        value /= 1024.0
    return f"{value:.1f} PB"

@router.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    mover = get_mover_parser()
    excl = get_exclusion_manager()
    
    radarr_connected = get_radarr_client().test_connection()
    sonarr_connected = get_sonarr_client().test_connection()
    
    mover_stats = mover.get_stats_for_file()
    excl_stats = excl.get_exclusion_stats()
    
    # Calculate Mover Health Stats
    ca_efficiency = mover_stats['efficiency'] if mover_stats else 0
    ca_mover_excluded = mover_stats['excluded'] if mover_stats else 0
    ca_mover_moved = mover_stats['moved'] if mover_stats else 0
    ca_space_saved = format_filesize(mover_stats['total_bytes_kept']) if mover_stats else "0 B"
    ca_mover_last_run = datetime.datetime.fromtimestamp(mover_stats['timestamp']).strftime('%Y-%m-%d %H:%M') if mover_stats else "Never"
    ca_mover_status = mover_stats['filename'] if mover_stats else "No logs found"
    
    # Last build time
    last_build = "Never"
    exclusions_file = "/config/mover_exclusions.txt"
    if os.path.exists(exclusions_file):
        last_build = datetime.datetime.fromtimestamp(os.path.getmtime(exclusions_file)).strftime('%Y-%m-%d %H:%M')
    
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "radarr_connected": radarr_connected,
        "sonarr_connected": sonarr_connected,
        "ca_efficiency": ca_efficiency,
        "ca_mover_excluded": ca_mover_excluded,
        "ca_mover_moved": ca_mover_moved,
        "ca_space_saved": ca_space_saved,
        "ca_mover_last_run": ca_mover_last_run,
        "ca_mover_status": ca_mover_status,
        "exclusion_count": excl_stats.get("total_count", 0),
        "last_build": last_build
    })
